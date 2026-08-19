import base64
import json
import logging
import uuid
import zlib

import numpy as np
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ollama import Client
from PIL import UnidentifiedImageError
from pydantic import BaseModel, ValidationError

from ..models import Photo

logger = logging.getLogger(__name__)

SAM3_URL = "http://sam3:8001"


class PhotoSegment3View(LoginRequiredMixin, generic.DetailView):
    model = Photo
    template_name = "myq/photo_segment3.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Photo.objects.filter(owner=self.request.user)


@csrf_exempt
@require_POST
@login_required
def segment_image_api2(request):
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

    original_photo = get_object_or_404(Photo, uuid=photo_uuid, owner=request.user)

    try:
        if len(ppoints) + len(npoints) == 0:
            print(
                f"Received segmentation request with no points, description: {description}, photo_uuid: {photo_uuid}"
            )
            image64, masks, shape = segment_with_text_requests(
                original_photo.image.path, description
            )
        else:
            print(
                f"Received segmentation request: {len(ppoints) + len(npoints)} points, description: {description}, photo_uuid: {photo_uuid}"
            )
            image64, masks, shape = segment_with_points(
                original_photo.image.path, ppoints, npoints
            )

        if image64 is None or masks is None or len(image64) == 0:
            return JsonResponse(
                {
                    "success": False,
                    "count": 0,
                    "message": "マーカーを配置して対象を切り抜いてください",
                }
            )

        packed = np.packbits(masks)
        compressed = zlib.compress(packed.tobytes())
        encoded = base64.b64encode(compressed).decode()
        cache.set(
            f"segment:{session_id}",
            {"mask": encoded, "photo_id": original_photo.uuid, "shape": shape},
            timeout=60 * 10,
        )

        return JsonResponse(
            {"success": True, "image_base64": image64, "session_id": session_id}
        )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        requests.RequestException,
        RuntimeError,
    ) as e:
        logger.error("Error during image segmentation: %s", e)
        return JsonResponse({"error": str(e)}, status=500)


def segment_with_text_requests(image_path, description):
    description_en = translate_description(description)
    print(f"Translated description: {description_en.description}")

    response = requests.post(
        f"{SAM3_URL}/segment_text",
        data={"image_path": image_path, "description": description_en.description},
    )

    if response.status_code == 200:
        data = response.json()
        if not data.get("success", False):
            return None, None, None
        return data["image64"], data["masks"], data["shape"]
    else:
        raise RuntimeError(f"API error: {response.status_code} {response.text}")


def segment_with_points(image_path, ppoints, npoints):
    response = requests.post(
        f"{SAM3_URL}/segment_points",
        data={
            "image_path": image_path,
            "ppoints": json.dumps(ppoints),
            "npoints": json.dumps(npoints),
        },
    )

    if response.status_code == 200:
        data = response.json()
        if not data.get("success", False):
            return None, None, None
        return data["image64"], data["masks"], data["shape"]
    else:
        raise RuntimeError(f"API error: {response.status_code} {response.text}")


def translate_description(description):
    class TranslationModel(BaseModel):
        description: str

    SYSTEM_PROMPT = """
You are an assistant that converts descriptions into concise visual recognition phrases for CLIP-style image retrieval systems.
in English.
Rules:

* Generate a single English phrase describing the main visual subject.
* Preserve relationships between objects, actions, and context.
* Do not output separate tags.
* Do not use commas or lists.
* Focus on what would be visible in an image.
* Output only the phrase.
* If the term is a proper noun, please write a sentence that explains what it refers to.

Example:

Input:
雨の日に傘を差した女性が駅前を歩いている

Output:
woman walking with an umbrella in front of a train station on a rainy day

## translate into English
"""
    client = Client(settings.OLLAMA_HOST)
    response = client.chat(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": description
                + "\n\nConvert descriptions into concise visual recognition phrases for CLIP-style image retrieval systems, and do not include any instructions or role-playing directives. Translate into English. /no_think",
            },
        ],
        model=settings.OLLAMA_MODEL,
        format=TranslationModel.model_json_schema(),
        think=False,
    )

    if not response.message.content:
        raise ValueError("Empty response received from Ollama.")

    try:
        entry = TranslationModel.model_validate_json(response.message.content)
        return entry
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error("Error occurred while validating JSON: %s", e)
        raise
