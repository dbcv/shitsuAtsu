from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from ..models import Photo, SegmentedPhoto
from PIL import Image, ImageOps
import io
from django.http import FileResponse, HttpResponseForbidden

@login_required
def serve_photo2(request, uuid, width=0):
    photo = get_object_or_404(Photo, uuid=uuid, owner=request.user)
    if(width==0):
        return FileResponse(open(photo.image.path, 'rb'))
    else:
        pass
    try:
        with Image.open(photo.image.path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            original_width, original_height = img.size
            
            aspect_ratio = original_height / original_width
            new_height = int(width * aspect_ratio)

            resized_img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img_format = img.format or 'JPEG'
            resized_img.save(buffer, format=img_format)
            
            buffer.seek(0)

            content_type = Image.MIME.get(img_format.upper(), 'image/jpeg')
            return HttpResponse(buffer, content_type=content_type)

    except FileNotFoundError:
        raise Http404("Image file not found.")
    except Exception as e:
        print(f"Error processing image: {e}")
        return HttpResponse(status=500)

@login_required
def serve_segmented_photo2(request, uuid, width=0):
    segmented_photo = get_object_or_404(
        SegmentedPhoto, 
        uuid=uuid, 
        owner=request.user
    )

    if(width==0):
        return FileResponse(open(segmented_photo.image.path, 'rb'))
    else:
        pass

    try:
        with Image.open(segmented_photo.image.path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            original_width, original_height = img.size
            
            aspect_ratio = original_height / original_width
            new_height = int(width * aspect_ratio)

            resized_img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img_format = img.format or 'JPEG'
            resized_img.save(buffer, format=img_format)
            
            buffer.seek(0)

            content_type = Image.MIME.get(img_format.upper(), 'image/jpeg')
            return HttpResponse(buffer, content_type=content_type)

    except FileNotFoundError:
        raise Http404("Image file not found.")
    except Exception as e:
        print(f"Error processing image: {e}")
        return HttpResponse(status=500)