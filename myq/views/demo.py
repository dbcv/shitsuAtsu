import base64
import io
import json
import logging
import uuid
import zipfile
import zlib

import numpy as np
import requests
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from PIL import Image, ImageOps

from ..models import Photo, SegmentedPhoto
from .segment import SAM3_URL, translate_description

logger = logging.getLogger(__name__)


class StaffRequiredMixin(UserPassesTestMixin):
    """管理者（is_staff または is_superuser）のみアクセス可能にするMixin"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("このデモページを利用するには管理者権限が必要です。")


def staff_required_api(view_func):
    """管理者専用API用デコレータ"""

    def _wrapped_view(request, *args, **kwargs):
        if not (
            request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        ):
            return JsonResponse(
                {"error": "管理者権限が必要です (Admin staff required)."}, status=403
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view


class DemoIndexView(StaffRequiredMixin, generic.TemplateView):
    """デモトップページ：全ユーザーの画像・セグメント一覧と各デモへのナビゲーション"""

    template_name = "myq/demo/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_filter = self.request.GET.get("user")
        search_query = self.request.GET.get("q", "")

        photos_qs = Photo.objects.select_related("owner").all().order_by("-uploaded_at")
        segmented_qs = (
            SegmentedPhoto.objects.select_related("owner", "original_photo")
            .all()
            .order_by("-created_at")
        )

        if user_filter:
            photos_qs = photos_qs.filter(owner__username=user_filter)
            segmented_qs = segmented_qs.filter(owner__username=user_filter)

        if search_query:
            photos_qs = photos_qs.filter(title__icontains=search_query)

        context["photos"] = photos_qs[:60]
        context["segmented_photos"] = segmented_qs[:60]
        context["all_users"] = User.objects.all().order_by("username")
        context["selected_user"] = user_filter
        context["search_query"] = search_query
        context["total_photos"] = Photo.objects.count()
        context["total_segmented"] = SegmentedPhoto.objects.count()
        return context


class DemoSegmentView(StaffRequiredMixin, generic.DetailView):
    """SAM3 セグメンテーション＆マスク素材出力デモ"""

    model = Photo
    template_name = "myq/demo/segment.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        # 全ユーザーのPhotoにアクセス可能
        return Photo.objects.all()


class DemoComparisonView(StaffRequiredMixin, generic.DetailView):
    """元画像・セグメント・レンダリング画像の比較＆一括エクスポートデモ"""

    model = Photo
    template_name = "myq/demo/comparison.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Photo.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo = self.get_object()
        # 関連する切り抜き画像を取得
        context["segmented_list"] = SegmentedPhoto.objects.filter(
            original_photo=photo
        ).order_by("-created_at")
        return context


class DemoRotationView(StaffRequiredMixin, generic.DetailView):
    """質感パラメータ調整＆物体回転アニメーション連番画像生成デモ"""

    model = SegmentedPhoto
    template_name = "myq/demo/rotation.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        # 全ユーザーのSegmentedPhotoにアクセス可能
        return SegmentedPhoto.objects.select_related("original_photo", "owner").all()


@csrf_exempt
@require_POST
@staff_required_api
def demo_segment_api(request):
    """管理者用 SAM3 セグメンテーションAPI
    ポジティブ/ネガティブ座標またはテキストから、
    - 透過切り抜きPNG (base64)
    - 2値白黒マスクPNG (base64)
    - マスク統計情報
    を返却します。
    """
    try:
        session_id = str(uuid.uuid4())
        ppoints_raw = request.POST.get("ppoints", "[]")
        npoints_raw = request.POST.get("npoints", "[]")
        description = request.POST.get("description", "")
        photo_uuid = request.POST.get("photo_uuid")

        if not photo_uuid:
            return JsonResponse({"error": "photo_uuid is required"}, status=400)

        ppoints = json.loads(ppoints_raw) if ppoints_raw else []
        npoints = json.loads(npoints_raw) if npoints_raw else []
    except (json.JSONDecodeError, TypeError) as e:
        return JsonResponse({"error": f"Invalid JSON in points: {e}"}, status=400)

    # 全ユーザーのPhotoから検索
    original_photo = get_object_or_404(Photo, uuid=photo_uuid)

    try:
        image_path = original_photo.image.path
        image_pil = Image.open(image_path)
        image_pil = ImageOps.exif_transpose(image_pil).convert("RGB")

        if len(ppoints) + len(npoints) == 0:
            if not description:
                description = original_photo.description or original_photo.title
            desc_obj = translate_description(description)
            res = requests.post(
                f"{SAM3_URL}/segment_text",
                data={"image_path": image_path, "description": desc_obj.description},
            )
        else:
            res = requests.post(
                f"{SAM3_URL}/segment_points",
                data={
                    "image_path": image_path,
                    "ppoints": json.dumps(ppoints),
                    "npoints": json.dumps(npoints),
                },
            )

        if res.status_code != 200:
            return JsonResponse({"error": f"SAM3 API error: {res.status_code} {res.text}"}, status=500)

        data = res.json()
        if not data.get("success", False):
            return JsonResponse({"success": False, "message": "対象が検出されませんでした。マーカーを追加してください。"})

        masks_raw = data.get("masks")
        if masks_raw is None:
            return JsonResponse({"success": False, "message": "マスクが生成されませんでした。"})

        mask_np = np.array(masks_raw, dtype=np.uint8)
        if mask_np.ndim > 2:
            mask_np = mask_np[0]

        # 1. 2値白黒マスク画像の生成 (Lモード, 0 or 255)
        binary_mask = (mask_np > 0).astype(np.uint8) * 255
        mask_pil = Image.fromarray(binary_mask, mode="L")
        mask_buffer = io.BytesIO()
        mask_pil.save(mask_buffer, format="PNG")
        mask_base64 = base64.b64encode(mask_buffer.getvalue()).decode()

        # 2. 透過切り抜き画像の生成 (RGBA)
        img_rgba = image_pil.convert("RGBA")
        img_np = np.array(img_rgba)
        cutout_np = np.zeros_like(img_np)
        cutout_np[mask_np > 0] = img_np[mask_np > 0]
        cutout_pil = Image.fromarray(cutout_np, mode="RGBA")
        cutout_buffer = io.BytesIO()
        cutout_pil.save(cutout_buffer, format="PNG")
        cutout_base64 = base64.b64encode(cutout_buffer.getvalue()).decode()

        # 3. 最小矩形バウンディングボックスの切り抜き
        coords = np.argwhere(mask_np > 0)
        bbox_base64 = ""
        bbox_info = {}
        if coords.size > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            cropped_bbox = cutout_pil.crop((int(x_min), int(y_min), int(x_max + 1), int(y_max + 1)))
            bbox_buf = io.BytesIO()
            cropped_bbox.save(bbox_buf, format="PNG")
            bbox_base64 = base64.b64encode(bbox_buf.getvalue()).decode()
            bbox_info = {
                "x_min": int(x_min),
                "y_min": int(y_min),
                "x_max": int(x_max),
                "y_max": int(y_max),
                "width": int(x_max - x_min + 1),
                "height": int(y_max - y_min + 1),
            }

        # キャッシュに保存（必要に応じたエクスポート用）
        packed = np.packbits(mask_np)
        compressed = zlib.compress(packed.tobytes())
        encoded = base64.b64encode(compressed).decode()
        cache.set(
            f"demo_segment:{session_id}",
            {
                "mask": encoded,
                "photo_id": str(original_photo.uuid),
                "shape": mask_np.shape,
            },
            timeout=60 * 30,
        )

        foreground_pixels = int(np.sum(mask_np > 0))
        total_pixels = mask_np.size

        return JsonResponse({
            "success": True,
            "session_id": session_id,
            "mask_base64": mask_base64,
            "cutout_base64": cutout_base64,
            "bbox_base64": bbox_base64,
            "bbox_info": bbox_info,
            "stats": {
                "foreground_pixels": foreground_pixels,
                "total_pixels": total_pixels,
                "percentage": round(foreground_pixels / total_pixels * 100, 2) if total_pixels > 0 else 0,
                "width": image_pil.width,
                "height": image_pil.height,
            }
        })

    except Exception:
        logger.exception("Error during demo segmentation")
        return JsonResponse({"error": "Error during demo segmentation"}, status=500)


@staff_required_api
def demo_export_comparison_zip(request, uuid):
    """元画像・セグメント・レンダリング画像およびメタデータをまとめた研究発表用ZIPを出力"""
    photo = get_object_or_404(Photo, uuid=uuid)
    segmented = SegmentedPhoto.objects.filter(original_photo=photo).order_by("-created_at").first()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. 元画像
        if photo.image:
            try:
                with open(photo.image.path, "rb") as f:
                    zip_file.writestr(f"original_{photo.uuid}.jpg", f.read())
            except OSError:
                pass

        # 2. セグメント画像
        if segmented and segmented.image:
            try:
                with open(segmented.image.path, "rb") as f:
                    zip_file.writestr(f"segmented_{segmented.uuid}.png", f.read())
            except OSError:
                pass

        # 3. 質感レンダリング画像
        if segmented and segmented.rendered_image:
            try:
                with open(segmented.rendered_image.path, "rb") as f:
                    zip_file.writestr(f"rendered_{segmented.uuid}.webp", f.read())
            except OSError:
                pass

        # 4. メタデータJSON
        metadata = {
            "title": photo.title,
            "original_filename": photo.original_filename,
            "description": photo.description,
            "owner": photo.owner.username,
            "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else "",
            "roughness": segmented.roughness if segmented else photo.roughness,
            "metalness": segmented.metalness if segmented else photo.metalness,
            "albedo": segmented.albedo if segmented else photo.albedo,
            "photo_uuid": str(photo.uuid),
            "segmented_uuid": str(segmented.uuid) if segmented else None,
        }
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="materials_{photo.uuid}.zip"'
    return response


@csrf_exempt
@require_POST
@staff_required_api
def demo_export_rotation_zip(request):
    """クライアント側でキャプチャされた360度回転連番画像（base64リスト）をZIPにまとめてダウンロード"""
    try:
        data = json.loads(request.body)
        frames = data.get("frames", [])
        title = data.get("title", "rotation_frames")
        meta = data.get("metadata", {})

        if not frames:
            return JsonResponse({"error": "No frames provided."}, status=400)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, frame_b64 in enumerate(frames):
                if "," in frame_b64:
                    frame_b64 = frame_b64.split(",")[1]
                frame_data = base64.b64decode(frame_b64)
                filename = f"frame_{idx:03d}.png"
                zip_file.writestr(filename, frame_data)

            # メタデータJSON
            if meta:
                zip_file.writestr("rotation_metadata.json", json.dumps(meta, indent=2, ensure_ascii=False))

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{title}.zip"'
        return response

    except Exception:
        logger.exception("Failed to export rotation zip")
        return JsonResponse({"error": "Failed to export rotation zip"}, status=500)
