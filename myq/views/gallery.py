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

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageOps
import base64
from ..apps import SAM2_PREDICTOR
import io
import numpy as np
from django.urls import reverse
from django.core.files.base import ContentFile
import uuid
from ..forms import SimpleSignUpForm

class PhotoGalleryView(LoginRequiredMixin, TemplateView):

    template_name = 'myq/gallery.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['original_photos'] = Photo.objects.filter(
            owner=self.request.user
        ).order_by('-uploaded_at')
        
        context['segmented_photos'] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')
        
        return context

class PhotoGallery2View(LoginRequiredMixin, TemplateView):

    template_name = 'myq/gallery2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['original_photos'] = Photo.objects.filter(
            owner=self.request.user
        ).order_by('-uploaded_at')
        
        context['segmented_photos'] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')
        
        return context

class PhotoGallery3View(LoginRequiredMixin, TemplateView):

    template_name = 'myq/gallery3.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['original_photos'] = Photo.objects.filter(
            owner=self.request.user
        ).order_by('-uploaded_at')
        
        context['segmented_photos'] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')
        
        return context
