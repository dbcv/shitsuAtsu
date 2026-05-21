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

class ThreeView(LoginRequiredMixin, generic.DetailView):
    model = SegmentedPhoto
    template_name = 'myq/reflectance.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return SegmentedPhoto.objects.filter(owner=self.request.user)