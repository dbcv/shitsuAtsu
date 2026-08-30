from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings
from django.urls import reverse


@override_settings(
    MIDDLEWARE=[
        m
        for m in settings.MIDDLEWARE
        if "AccessLogMiddleware" not in m and "TimingMiddleware" not in m
    ],
    SUPPORT_EMAIL="test-support@example.com",
)
class LoginViewTests(SimpleTestCase):
    def test_login_page_renders_dialog_and_support_email(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "パスワードを忘れた場合")
        self.assertContains(response, "forgot-password-dialog")
        self.assertContains(response, "test-support@example.com")
        self.assertContains(response, "ユーザー名")
        self.assertContains(response, "メールアドレス")



@override_settings(
    MIDDLEWARE=[
        m
        for m in settings.MIDDLEWARE
        if "AccessLogMiddleware" not in m and "TimingMiddleware" not in m
    ],
)
class GalleryViewTests(SimpleTestCase):
    def test_gallery_template_renders_dialog_and_buttons(self):
        dummy_photo = type(
            "PhotoStub",
            (),
            {
                "uuid": "00000000-0000-0000-0000-000000000001",
                "get_image_url_256": "/media/dummy_256.jpg",
                "title": "dummy photo",
            },
        )()
        rendered = render_to_string(
            "myq/gallery.html",
            {
                "original_photos": [dummy_photo],
                "segmented_photos": [],
                "csrf_token": "dummy_token",
            },
        )
        self.assertIn("image-modal", rendered)
        self.assertIn("modal-delete-btn", rendered)
        self.assertIn("modal-edit-link", rendered)
        self.assertIn("gallery-item-btn", rendered)


@override_settings(
    MIDDLEWARE=[
        m
        for m in settings.MIDDLEWARE
        if "AccessLogMiddleware" not in m and "TimingMiddleware" not in m
    ],
)
class PhotoSegment3Tests(SimpleTestCase):
    def test_segment_template_renders_no_detection_dialog(self):
        rendered = render_to_string(
            "myq/photo_segment3.html",
            {
                "object": type(
                    "PhotoStub",
                    (),
                    {
                        "uuid": "dummy-uuid",
                        "get_image_url": "/media/dummy.jpg",
                        "description": "test description",
                    },
                )(),
                "csrf_token": "dummy_token",
            },
        )
        self.assertIn("no-detection-dialog", rendered)
        self.assertIn("マーカーを配置して対象を切り抜いてください", rendered)
        self.assertIn("close-no-detection-btn", rendered)
