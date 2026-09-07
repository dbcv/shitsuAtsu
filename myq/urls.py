# myq/urls.py
from django.urls import path, re_path

from .views import demo
from .views.autoLogin import auto_login_view
from .views.gallery import PhotoGallery2View, PhotoGallery3View, PhotoGalleryView
from .views.homemenu import Home3View, Start3View
from .views.iconserve import faviconserve
from .views.photoserve import (
    serve_photo2,
    serve_rendered_photo2,
    serve_segmented_photo2,
)
from .views.reflectance import ThreeView, register_reflectance
from .views.segment import PhotoSegment3View, segment_image_api2
from .views.views import PhotoUploadView, delete_image_api, save_segmented_image

urlpatterns = [
    path("", Home3View.as_view(), name="home"),
    path("home2/", Home3View.as_view(), name="home2"),
    path("start/", Start3View.as_view(), name="start"),
    path("upload/", PhotoUploadView.as_view(), name="upload"),
    path(
        "photos/<uuid:uuid>/segment/", PhotoSegment3View.as_view(), name="photo_segment"
    ),
    re_path(
        r"^photos/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:-(?P<width>\d+))?\.(?P<ext>jpg|jpeg|png|webp)$",
        serve_photo2,
        name="serve_photo",
    ),
    path("api/segment2/", segment_image_api2, name="api_segment_image2"),
    path("api/save_segment/", save_segmented_image, name="api_save_segment"),
    re_path(
        r"^segmented_photos/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:-(?P<width>\d+))?\.(?P<ext>jpg|jpeg|png|webp)$",
        serve_segmented_photo2,
        name="serve_segmented_photo",
    ),
    re_path(
        r"^rendered_photos/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:-(?P<width>\d+))?\.(?P<ext>jpg|jpeg|png|webp)$",
        serve_rendered_photo2,
        name="serve_rendered_photo",
    ),
    path("gallery/", PhotoGalleryView.as_view(), name="photo_gallery"),
    path("gallery2/", PhotoGallery2View.as_view(), name="photo_gallery2"),
    path("gallery3/", PhotoGallery3View.as_view(), name="photo_gallery3"),
    path("api/delete_image/", delete_image_api, name="api_delete_image"),
    path("autologin/", auto_login_view, name="auto_login"),
    path("favicon.ico", faviconserve, name="faviconserve"),
    path("reflectance/<uuid:uuid>/", ThreeView.as_view(), name="reflectance_view"),
    path(
        "api/register_reflectance/", register_reflectance, name="register_reflectance"
    ),
    # Demo System for Research Presentation
    path("demo/", demo.DemoIndexView.as_view(), name="demo_index"),
    path("demo/segment/<uuid:uuid>/", demo.DemoSegmentView.as_view(), name="demo_segment"),
    path("demo/comparison/<uuid:uuid>/", demo.DemoComparisonView.as_view(), name="demo_comparison"),
    path("demo/rotation/<uuid:uuid>/", demo.DemoRotationView.as_view(), name="demo_rotation"),
    path("demo/api/segment/", demo.demo_segment_api, name="demo_api_segment"),
    path("demo/api/export_comparison/<uuid:uuid>/", demo.demo_export_comparison_zip, name="demo_export_comparison"),
    path("demo/api/export_rotation/", demo.demo_export_rotation_zip, name="demo_export_rotation"),
]
