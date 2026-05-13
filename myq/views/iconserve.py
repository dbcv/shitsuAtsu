from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from ..models import Photo, SegmentedPhoto
from PIL import Image, ImageOps
import io
from django.http import FileResponse, HttpResponseForbidden
from django.templatetags.static import static
from django.http import FileResponse, Http404
from django.contrib.staticfiles import finders

def faviconserve(request):
    image_path = finders.find('image/favicon.ico')
    if not image_path:
        raise Http404("404 not found")

    return FileResponse(open(str(image_path), 'rb'))