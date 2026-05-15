# myq/views.py
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

class SignUpView(generic.CreateView):
    form_class = SimpleSignUpForm
    success_url = reverse_lazy('login')
    template_name = 'myq/signup.html'

class PhotoUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'myq/upload.html'

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('image')
        description = request.POST.get('description')
        print(f"Received file: {file}, description: {description}")  # デバッグ用ログ
        if not file:
            return JsonResponse({'error': 'ファイルが選択されていません。'}, status=400)

        try:
            original_name = file.name
            file_title = os.path.splitext(original_name)[0]

            photo = Photo(
                image=file,
                title=description,
                original_filename=original_name,
                owner=request.user
            )
            photo.save()

            segment_url = reverse('photo_segment', kwargs={'uuid': photo.uuid})

            return JsonResponse({
                'success': True,
                'segment_url': segment_url 
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@login_required
def serve_photo(request, uuid):
    photo = get_object_or_404(Photo, uuid=uuid, owner=request.user)
    return FileResponse(open(photo.image.path, 'rb'))


class PhotoSegmentView(LoginRequiredMixin, generic.DetailView):
    model = Photo
    template_name = 'myq/photo_segment.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return Photo.objects.filter(owner=self.request.user)

@require_POST
@login_required
def save_segmented_image(request):
    try:
        photo_uuid = request.POST.get('photo_uuid')
        image_base64_data = request.POST.get('image_base64')

        if not photo_uuid or not image_base64_data:
            return JsonResponse({'error': '必要なデータが不足しています。'}, status=400)

        original_photo = get_object_or_404(Photo, uuid=photo_uuid, owner=request.user)

        format, imgstr = image_base64_data.split(';base64,') 
        ext = format.split('/')[-1]
        image_data = ContentFile(base64.b64decode(imgstr), name=f'seg_{uuid.uuid4()}.{ext}')

        segmented_photo = SegmentedPhoto(
            original_photo=original_photo,
            image=image_data,
            owner=original_photo.owner
        )
        segmented_photo.save()

        saved_image_url = segmented_photo.get_image_url()

        return JsonResponse({
            'success': True, 
            'message': '切り抜き画像を保存しました。',
            'url': saved_image_url
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def serve_segmented_photo(request, uuid):
    segmented_photo = get_object_or_404(
        SegmentedPhoto, 
        uuid=uuid, 
        owner=request.user
    )

    return FileResponse(open(segmented_photo.image.path, 'rb'))


@require_POST 
@login_required
def delete_image_api(request):

    try:
       
        image_uuid = request.POST.get('uuid')
        image_type = request.POST.get('type')

        if not image_uuid or not image_type:
            return JsonResponse({'error': '不正なリクエストです。'}, status=400)

        if image_type == 'original':
            model = Photo
            lookup = {'uuid': image_uuid, 'owner': request.user}
        elif image_type == 'segmented':
            model = SegmentedPhoto
            lookup = {'uuid': image_uuid, 'owner': request.user}
        else:
            return JsonResponse({'error': '未知の画像タイプです。'}, status=400)
        
        image_to_delete = get_object_or_404(model, **lookup)
        
        image_to_delete.delete()
        
        return JsonResponse({'success': True, 'message': '画像を削除しました。'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)