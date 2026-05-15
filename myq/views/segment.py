from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from ..models import Photo, SegmentedPhoto
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
import os
import torch
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageOps
import base64
from ..apps import SAM2_PREDICTOR, SAM3_PROCESSOR
import io
import numpy as np
from django.urls import reverse
from django.core.files.base import ContentFile
import uuid
from ..forms import SimpleSignUpForm
import json


class PhotoSegment3View(LoginRequiredMixin, generic.DetailView):
    model = Photo
    template_name = 'myq/photo_segment3.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return Photo.objects.filter(owner=self.request.user)


def apply_mask_to_cutout(original_image, mask):
    mask_bool = mask > 0

    img_rgba = original_image.convert("RGBA")
    img_np = np.array(img_rgba)

    h, w, _ = img_np.shape
    new_img_np = np.zeros_like(img_np)

    new_img_np[mask_bool] = img_np[mask_bool]

    return Image.fromarray(new_img_np)

def max_square_submatrix(matrix: np.ndarray) -> np.ndarray:
    n, m = matrix.shape
    dp = np.zeros((n, m), dtype=int)

    max_size = 0
    candidates = []

    for i in range(n):
        for j in range(m):
            if matrix[i, j] == 1:
                if i == 0 or j == 0:
                    dp[i, j] = 1
                else:
                    dp[i, j] = min(dp[i-1, j], dp[i, j-1], dp[i-1, j-1]) + 1

                if dp[i, j] > max_size:
                    max_size = dp[i, j]
                    candidates = [(i, j)]
                elif dp[i, j] == max_size:
                    candidates.append((i, j))

    if max_size == 0:
        return np.zeros_like(matrix)

    center = np.array([n/2, m/2])
    best_pos = (0,0)
    best_dist = float("inf")

    for (i, j) in candidates:
        half = max_size / 2
        square_center = np.array([i - half + 0.5, j - half + 0.5])
        dist = np.linalg.norm(square_center - center)
        if dist < best_dist:
            best_dist = dist
            best_pos = (i, j)

    result = np.zeros_like(matrix)
    i, j = best_pos
    for r in range(i - max_size + 1, i + 1):
        for c in range(j - max_size + 1, j + 1):
            result[r, c] = 1

    return result

def crop_with_mask(image: Image.Image, mask: np.ndarray) -> Image.Image:
    """
    マスクが1の部分を含む最小矩形で画像をクロップする
    - image: PIL.Image.Image
    - mask:  2D numpy array (0 or 1), 正方形
    
    return: PIL.Image.Image（クロップ後）
    """
    coords = np.argwhere(mask == 1)
    if coords.size == 0:
        raise ValueError("マスクに1が含まれていません")
    
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    
    h, w = mask.shape
    if (image.width, image.height) != (w, h):
        mask_h, mask_w = mask.shape
        scale_x = image.width / mask_w
        scale_y = image.height / mask_h
        x_min = int(x_min * scale_x)
        x_max = int((x_max + 1) * scale_x)
        y_min = int(y_min * scale_y)
        y_max = int((y_max + 1) * scale_y)

    cropped = image.crop((x_min, y_min, x_max, y_max))
    return cropped

def convert_to_optimized_bw(image: Image.Image) -> Image.Image:

    try:
        img = image.convert("RGBA")

        # 2. アルファチャンネルを取得する
        # alphaチャンネルは、透明なピクセルが0(黒)、不透明なピクセルが255(白)になる
        alpha = img.getchannel('A')

        # 3. 色を反転させる (白黒反転)
        # これで、透明だった部分が白(255)、不透明だった部分が黒(0)になる
        # Pillowの機能を使えば、各ピクセルを自分でループ処理する必要がない
        inverted_alpha = Image.eval(alpha, lambda a: 255 - a)

        # 4. 2値画像('1')に変換してファイルサイズを最小化する
        # '1'モードは1ピクセルを1ビットで表現するため、データ量が非常に小さい
        # dither=Image.NONE を指定して、中間色を作らないようにする
        final_image = inverted_alpha.convert('1', dither=Image.Dither.NONE)

        # 5. 最適化オプションを有効にして保存
        return final_image
        final_image.save(output_path, 'PNG', optimize=True)
        print(f"画像を変換し、'{output_path}' に保存しました。")

    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません")
        return image
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return image

@csrf_exempt
@require_POST
@login_required
def segment_image_api2(request):
    if SAM3_PROCESSOR is None:
        return JsonResponse({'error': 'Model not loaded'}, status=503)

    try:
        ppoints = json.loads(request.POST.get('ppoints'))
        npoints = json.loads(request.POST.get('npoints'))
        description = request.POST.get('description')
        input_point = []
        input_label = []
        for p in ppoints:
            input_point.append([p["x"],p["y"]])
            input_label.append(1)
        for p in npoints:
            input_point.append([p["x"],p["y"]])
            input_label.append(0)
        
        photo_uuid = request.POST.get('photo_uuid')

        original_photo = get_object_or_404(Photo, uuid=photo_uuid, owner=request.user)
        
        image_pil_raw = Image.open(original_photo.image.path)
        
        image_pil = ImageOps.exif_transpose(image_pil_raw).convert("RGB")
        
        
        with torch.autocast("cuda", dtype=torch.bfloat16):
            inference_state = SAM3_PROCESSOR.set_image(image_pil)
            output = SAM3_PROCESSOR.set_text_prompt(state=inference_state, prompt=description)
        
        input_point = np.array(input_point)
        input_label = np.array(input_label)

        image64 = []

        masks, boxes, scores = output["masks"], output["boxes"], output["scores"]
        
        m = output["masks"]
        print(m)
        print("type(output['masks']):", type(m))

        if hasattr(m, "shape"):
            print("output['masks'].shape:", m.shape, "dtype:", getattr(m, "dtype", None))

        mask_np = masks.squeeze().detach().cpu().numpy()

        masks = mask_np.astype(np.uint8)

        print("masks shape:", masks.shape, "dtype:", masks.dtype)

        buffered = io.BytesIO()
        image = apply_mask_to_cutout(image_pil, masks)
        image = convert_to_optimized_bw(image)
        image.save(buffered, format="PNG", optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        image64.append(img_str)

        buffered2 = io.BytesIO()
        image2 = crop_with_mask(image_pil,max_square_submatrix(masks))
        image2.save(buffered2, format="PNG", optimize=True)
        img_str2 = base64.b64encode(buffered2.getvalue()).decode()
        
        print(masks)
        masks = masks.tolist()
        return JsonResponse({'success': True, 'image_base64': image64, 'crop' : img_str2})

    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)

from django.http import StreamingHttpResponse
from django.views.decorators.http import require_POST
import json, time