import base64
import io
import json
import os
import uuid
import zlib

import numpy as np
import requests
import torch
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, TemplateView
from PIL import Image, ImageOps

from ..forms import SimpleSignUpForm
from ..models import Photo, SegmentedPhoto
from ..tasks import crop

SAM3_URL = "http://sam3:8001"

class PhotoSegment3View(LoginRequiredMixin, generic.DetailView):
    model = Photo
    template_name = 'myq/photo_segment3.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return Photo.objects.filter(owner=self.request.user)

@csrf_exempt
@require_POST
@login_required
def segment_image_api2(request):
    try:
        session_id = str(uuid.uuid4())
        ppoints = json.loads(request.POST.get('ppoints'))
        npoints = json.loads(request.POST.get('npoints'))
        description = request.POST.get('description')
        photo_uuid = request.POST.get('photo_uuid')

        original_photo = get_object_or_404(Photo, uuid=photo_uuid, owner=request.user)
        image_pil_raw = Image.open(original_photo.image.path)
        image_pil = ImageOps.exif_transpose(image_pil_raw).convert("RGB")

        if len(ppoints) + len(npoints) == 0:
            print(f"Received segmentation request with no points, description: {description}, photo_uuid: {photo_uuid}")
            image64, masks, shape = segment_with_text_requests(original_photo.image.path, description)
        else:
            print(f"Received segmentation request: {len(ppoints) + len(npoints)} points, description: {description}, photo_uuid: {photo_uuid}")
            image64, masks, shape = segment_with_points(image_pil, ppoints, npoints)

        packed = np.packbits(masks)
        compressed = zlib.compress(packed.tobytes())
        encoded = base64.b64encode(compressed).decode()
        cache.set(
            f"segment:{session_id}",
            {
                "mask": encoded,
                "photo_id": original_photo.id,
                "shape": shape
            },
            timeout=60 * 10
        )
        
        return JsonResponse({'success': True, 'image_base64': image64, 'session_id': session_id})

    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)
    
def segment_with_text_requests(image_path, description):

    response = requests.post(
        f"{SAM3_URL}/segment_text",
        data={
            "image_path": image_path,
            "description": description
        }
    )

    if response.status_code == 200:
        data = response.json()
        return data["image64"], data["masks"], data["shape"]
    else:
        raise Exception(f"API error: {response.status_code} {response.text}")

def segment_with_points(image_pil, ppoints, npoints):
    input_point = []
    input_label = []
    for p in ppoints:
        input_point.append([p["x"],p["y"]])
        input_label.append(1)
    for p in npoints:
        input_point.append([p["x"],p["y"]])
        input_label.append(0)
    
    input_point = np.array(input_point)
    input_label = np.array(input_label)
    return

import json
import time

from django.http import StreamingHttpResponse
from django.views.decorators.http import require_POST
