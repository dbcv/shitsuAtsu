from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from ..models import Photo, SegmentedPhoto


class PhotoGalleryView(LoginRequiredMixin, TemplateView):
    template_name = "myq/gallery.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["original_photos"] = Photo.objects.filter(
            owner=self.request.user
        ).order_by("-uploaded_at")

        context["segmented_photos"] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by("-created_at")

        return context


class PhotoGallery2View(LoginRequiredMixin, TemplateView):
    template_name = "myq/gallery2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["original_photos"] = Photo.objects.filter(
            owner=self.request.user
        ).order_by("-uploaded_at")

        context["segmented_photos"] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by("-created_at")

        return context


class PhotoGallery3View(LoginRequiredMixin, TemplateView):
    template_name = "myq/gallery3.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["original_photos"] = Photo.objects.filter(
            owner=self.request.user
        ).order_by("-uploaded_at")

        context["segmented_photos"] = SegmentedPhoto.objects.filter(
            owner=self.request.user
        ).order_by("-created_at")

        return context
