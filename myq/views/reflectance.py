import base64
import json
import logging
import uuid

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import DatabaseError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.decorators.http import require_POST

from ..models import SegmentedPhoto

logger = logging.getLogger(__name__)


class ThreeView(LoginRequiredMixin, generic.DetailView):
    model = SegmentedPhoto
    template_name = "myq/reflectance.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        try:
            return SegmentedPhoto.objects.filter(owner=self.request.user)
        except (ProgrammingError, DatabaseError):
            return SegmentedPhoto.objects.filter(owner=self.request.user).defer("rendered_image")


@require_POST
@login_required
def register_reflectance(request):
    try:
        data = json.loads(request.body)
        photo_uuid = data["photo_uuid"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return JsonResponse({"status": "error", "message": f"Invalid request data: {e}"}, status=400)

    try:
        photo = SegmentedPhoto.objects.get(uuid=photo_uuid, owner=request.user)
    except (ProgrammingError, DatabaseError):
        photo = get_object_or_404(SegmentedPhoto.objects.defer("rendered_image"), uuid=photo_uuid, owner=request.user)
    except SegmentedPhoto.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Photo not found"}, status=404)

    try:
        photo.roughness = data.get("roughness")
        photo.metalness = data.get("metalness")
        albedo = data.get("albedo")
        if albedo and not str(albedo).startswith("#"):
            albedo = f"#{albedo}"
        photo.albedo = albedo

        update_fields = ["roughness", "metalness", "albedo"]

        capture_image_data = data.get("capture_image")
        if capture_image_data and isinstance(capture_image_data, str) and capture_image_data.startswith("data:image"):
            try:
                format_info, img_str = capture_image_data.split(";base64,")
                ext = "webp" if "webp" in format_info else "png"
                decoded_img = base64.b64decode(img_str)
                filename = f"{uuid.uuid4()}.{ext}"
                if photo.has_rendered_image:
                    photo.rendered_image.delete(save=False)
                photo.rendered_image.save(filename, ContentFile(decoded_img), save=False)
                update_fields.append("rendered_image")
            except (ValueError, TypeError, OSError) as e:
                logger.error("Failed to decode rendered capture: %s", e)

        try:
            photo.save(update_fields=update_fields)
        except (ProgrammingError, DatabaseError):
            photo.save(update_fields=["roughness", "metalness", "albedo"])

        return JsonResponse(
            {
                "status": "success",
                "message": "Reflectance data registered successfully.",
            }
        )
    except (ValidationError, DatabaseError, ValueError) as e:
        logger.error("Failed to save reflectance data: %s", e)
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

