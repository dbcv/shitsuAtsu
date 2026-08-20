import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError, ProgrammingError
from django.views.generic import RedirectView, TemplateView

from ..models import Photo, SegmentedPhoto

logger = logging.getLogger(__name__)


class PhotoGalleryView(LoginRequiredMixin, TemplateView):
    template_name = "myq/gallery.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["original_photos"] = Photo.objects.filter(
            owner=self.request.user
        ).order_by("-uploaded_at")

        try:
            context["segmented_photos"] = list(
                SegmentedPhoto.objects.filter(
                    owner=self.request.user
                ).order_by("-created_at")
            )
        except (ProgrammingError, DatabaseError) as e:
            logger.warning("rendered_image column not available, fallback to cutout image: %s", e)
            try:
                context["segmented_photos"] = list(
                    SegmentedPhoto.objects.filter(
                        owner=self.request.user
                    ).defer("rendered_image").order_by("-created_at")
                )
            except (ProgrammingError, DatabaseError):
                context["segmented_photos"] = []

        return context


class PhotoGallery2View(RedirectView):
    permanent = False
    url = "/gallery/#original"


class PhotoGallery3View(RedirectView):
    permanent = False
    url = "/gallery/#segmented"
