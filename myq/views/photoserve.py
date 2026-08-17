import io
import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from PIL import Image, ImageOps, UnidentifiedImageError

from ..models import Photo, SegmentedPhoto

logger = logging.getLogger(__name__)


@login_required
def serve_photo2(request, uuid, width=0, ext="png"):
    photo = get_object_or_404(Photo, uuid=uuid, owner=request.user)
    try:
        with Image.open(photo.image.path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            original_width, original_height = img.size

            aspect_ratio = original_height / original_width
            width = int(width)
            if width == 0:
                width = original_width
            new_height = int(width * aspect_ratio)

            resized_img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img_format = (
                ext.upper() if ext.lower() in ["jpg", "jpeg", "png", "webp"] else "PNG"
            )
            resized_img.save(buffer, format=img_format)

            buffer.seek(0)

            content_type = Image.MIME.get(img_format.upper(), "image/jpeg")
            return HttpResponse(buffer, content_type=content_type)

    except FileNotFoundError:
        raise Http404("Image file not found.")
    except (UnidentifiedImageError, OSError, ValueError) as e:
        logger.error("Error processing image: %s", e)
        return HttpResponse(status=500)


@login_required
def serve_segmented_photo2(request, uuid, width=0, ext="png"):
    segmented_photo = get_object_or_404(SegmentedPhoto, uuid=uuid, owner=request.user)

    try:
        with Image.open(segmented_photo.image.path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            original_width, original_height = img.size

            aspect_ratio = original_height / original_width
            width = int(width)
            if width == 0:
                width = original_width
            new_height = int(width * aspect_ratio)

            resized_img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img_format = (
                ext.upper() if ext.lower() in ["jpg", "jpeg", "png", "webp"] else "PNG"
            )
            resized_img.save(buffer, format=img_format)

            buffer.seek(0)

            content_type = Image.MIME.get(img_format.upper(), "image/jpeg")
            return HttpResponse(buffer, content_type=content_type)

    except FileNotFoundError:
        raise Http404("Image file not found.")
    except (UnidentifiedImageError, OSError, ValueError) as e:
        logger.error("Error processing image: %s", e)
        return HttpResponse(status=500)

