# myq/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views.views import PhotoUploadView,\
    serve_photo, save_segmented_image,\
    serve_segmented_photo, delete_image_api

from .views.gallery import PhotoGalleryView, PhotoGallery2View, PhotoGallery3View
from .views.segment import PhotoSegment3View, segment_image_api2
from .views.homemenu import SignUpView, HomeView, Home2View, Home3View, Start3View
from .views.autoLogin import auto_login_view
from .views.photoserve import serve_photo2, serve_segmented_photo2
from .views.iconserve import faviconserve

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('home2/', Home3View.as_view(), name='home2'),
    path('home-old01/', Home2View.as_view(), name='home3'),
    path("start/", Start3View.as_view(), name="start"),
    path('upload/', PhotoUploadView.as_view(), name='upload'),
    path('photos/<uuid:uuid>/segment/', PhotoSegment3View.as_view(), name='photo_segment'),
    path('photos/<uuid:uuid>.png', serve_photo, name='serve_photo'),
    path('photos/<uuid:uuid>-<int:width>.png', serve_photo2, name='serve_photo2'),
    path('api/segment2/', segment_image_api2, name='api_segment_image2'),
    path('api/save_segment/', save_segmented_image, name='api_save_segment'),
    path('segmented_photo/<uuid:uuid>.png', serve_segmented_photo, name='serve_segmented_photo'),
    path('segmented_photo/<uuid:uuid>-<int:width>.png', serve_segmented_photo2, name='serve_segmented_photo2'),
    path('gallery/', PhotoGalleryView.as_view(), name='photo_gallery'),
    path('gallery2/', PhotoGallery2View.as_view(), name='photo_gallery2'),
    path('gallery3/', PhotoGallery3View.as_view(), name='photo_gallery3'),
    path('api/delete_image/', delete_image_api, name='api_delete_image'),
    path('autologin/', auto_login_view, name='auto_login'),
    path('favicon.ico', faviconserve, name='faviconserve'),
]