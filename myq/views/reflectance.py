import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import DatabaseError
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
        return SegmentedPhoto.objects.filter(owner=self.request.user)


@require_POST
@login_required
def register_reflectance(request):
    try:
        data = json.loads(request.body)
        photo_uuid = data["photo_uuid"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return JsonResponse({"status": "error", "message": f"Invalid request data: {e}"}, status=400)

    photo = get_object_or_404(SegmentedPhoto, uuid=photo_uuid, owner=request.user)

    try:
        photo.roughness = data.get("roughness")
        photo.metalness = data.get("metalness")
        albedo = data.get("albedo")
        if albedo and not str(albedo).startswith("#"):
            albedo = f"#{albedo}"
        photo.albedo = albedo
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

