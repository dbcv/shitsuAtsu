from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Photo, SegmentedPhoto
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