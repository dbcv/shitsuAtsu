from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404


def faviconserve(request):
    image_path = finders.find("image/favicon.ico")
    if not image_path:
        raise Http404("404 not found")

    return FileResponse(open(str(image_path), "rb"))
