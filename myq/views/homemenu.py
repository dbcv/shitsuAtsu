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
from django.templatetags.static import static

class SignUpView(generic.CreateView):
    form_class = SimpleSignUpForm
    success_url = reverse_lazy('login')
    template_name = 'myq/signup.html'

class HomeView(TemplateView):
    template_name = 'myq/home.html'

class Home2View(LoginRequiredMixin, TemplateView):
    template_name = 'myq/home2.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        

        context['segmented_photos'] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')
        image_count = len(context['segmented_photos'])
        image_url = static(f'image/tree/{("000"+str(int(image_count/4)))[-3:]}.png')

        context['count_segment'] = [{"imgurl":image_url, "count":image_count}]
        return context

class Home3View(LoginRequiredMixin, TemplateView):
    template_name = 'myq/home3.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        

        context['segmented_photos'] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by('-created_at')
        image_count = len(context['segmented_photos'])
        image_url = static(f'image/tree/{("000"+str(int(image_count/4)))[-3:]}.png')

        context['count_segment'] = [{"imgurl":image_url, "count":image_count}]
        return context

class Start3View(LoginRequiredMixin, TemplateView):
    template_name = 'myq/start3.html'