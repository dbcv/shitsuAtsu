import io
import logging

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, ProgrammingError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from PIL import Image, ImageOps, UnidentifiedImageError

from ..models import Photo, SegmentedPhoto

logger = logging.getLogger(__name__)


def _resize_and_serve_image(image_path, width=0, ext="webp"):
    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img)

        img_format = (
            ext.upper() if ext.lower() in ["jpg", "jpeg", "png", "webp"] else "WEBP"
        )

        has_alpha = (
            img.mode in ("RGBA", "LA")
            or (img.mode == "P" and "transparency" in img.info)
        )

        if has_alpha and img_format in ("PNG", "WEBP"):
            img = img.convert("RGBA")
        elif has_alpha and img_format in ("JPG", "JPEG"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.convert("RGBA").split()[3])
            img = bg
        else:
            img = img.convert("RGB")

        original_width, original_height = img.size
        width = int(width)
        if width <= 0 or width >= original_width:
            resized_img = img
        else:
            aspect_ratio = original_height / original_width
            new_height = max(1, int(width * aspect_ratio))
            resized_img = img.resize((width, new_height), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        resized_img.save(buffer, format=img_format)
        buffer.seek(0)

        content_type = Image.MIME.get(img_format.upper(), "image/webp")
        return HttpResponse(buffer, content_type=content_type)


@login_required
def serve_photo2(request, uuid, width=0, ext="png"):
    photo = get_object_or_404(Photo, uuid=uuid, owner=request.user)
    try:
        return _resize_and_serve_image(photo.image.path, width=width, ext=ext)
    except FileNotFoundError:
        raise Http404("Image file not found.")
    except (UnidentifiedImageError, OSError, ValueError) as e:
        logger.error("Error processing image: %s", e)
        return HttpResponse(status=500)


@login_required
def serve_segmented_photo2(request, uuid, width=0, ext="png"):
    try:
        segmented_photo = get_object_or_404(SegmentedPhoto, uuid=uuid, owner=request.user)
    except (ProgrammingError, DatabaseError):
        segmented_photo = get_object_or_404(SegmentedPhoto.objects.defer("rendered_image"), uuid=uuid, owner=request.user)

    try:
        return _resize_and_serve_image(segmented_photo.image.path, width=width, ext=ext)
    except FileNotFoundError:
        raise Http404("Image file not found.")
    except (UnidentifiedImageError, OSError, ValueError) as e:
        logger.error("Error processing image: %s", e)
        return HttpResponse(status=500)


@login_required
def serve_rendered_photo2(request, uuid, width=0, ext="webp"):
    try:
        segmented_photo = get_object_or_404(SegmentedPhoto, uuid=uuid, owner=request.user)
        target_field = (
            segmented_photo.rendered_image
            if segmented_photo.has_rendered_image
            else segmented_photo.image
        )
    except (ProgrammingError, DatabaseError):
        segmented_photo = get_object_or_404(SegmentedPhoto.objects.defer("rendered_image"), uuid=uuid, owner=request.user)
        target_field = segmented_photo.image

    try:
        return _resize_and_serve_image(target_field.path, width=width, ext=ext)
    except FileNotFoundError:
        raise Http404("Image file not found.")
    except (UnidentifiedImageError, OSError, ValueError) as e:
        logger.error("Error processing image: %s", e)
        return HttpResponse(status=500)


