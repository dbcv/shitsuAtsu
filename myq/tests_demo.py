from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Photo, SegmentedPhoto


class DemoSystemTests(TestCase):
    def setUp(self):
        # 1. 一般ユーザーと管理者ユーザーを作成
        self.normal_user = User.objects.create_user(
            username="normaluser", password="password123", is_staff=False
        )
        self.staff_user = User.objects.create_user(
            username="staffadmin", password="password123", is_staff=True
        )

        # 2. テスト用画像データを作成
        dummy_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9",
            content_type="image/jpeg",
        )

        self.photo = Photo.objects.create(
            title="テスト研究素材",
            image=dummy_image,
            owner=self.normal_user,
            original_filename="test_image.jpg",
            description="金属のカップ",
            roughness=0.25,
            metalness=0.85,
            albedo="#c0c0c0",
        )

        self.segmented = SegmentedPhoto.objects.create(
            original_photo=self.photo,
            owner=self.normal_user,
            image=dummy_image,
            roughness=0.25,
            metalness=0.85,
            albedo="#c0c0c0",
        )

        self.client = Client()

    def test_demo_access_denied_for_anonymous(self):
        """未ログインユーザーはアクセス拒否（403またはリダイレクト）されること"""
        response = self.client.get(reverse("demo_index"))
        self.assertEqual(response.status_code, 403)

    def test_demo_access_denied_for_normal_user(self):
        """一般ユーザーはデモページにアクセスできないこと（403）"""
        self.client.login(username="normaluser", password="password123")
        response = self.client.get(reverse("demo_index"))
        self.assertEqual(response.status_code, 403)

        # 個別デモページも拒否されること
        response_seg = self.client.get(reverse("demo_segment", kwargs={"uuid": self.photo.uuid}))
        self.assertEqual(response_seg.status_code, 403)

    def test_demo_access_allowed_for_staff_user(self):
        """管理者ユーザーはデモページにアクセスでき、全ユーザーのデータが表示されること"""
        self.client.login(username="staffadmin", password="password123")

        # 1. デモトップ
        response = self.client.get(reverse("demo_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "テスト研究素材")
        self.assertContains(response, "@normaluser")

        # 2. SAM3 セグメント画面
        response_seg = self.client.get(reverse("demo_segment", kwargs={"uuid": self.photo.uuid}))
        self.assertEqual(response_seg.status_code, 200)
        self.assertContains(response_seg, "SAM3 セグメンテーション＆マスク出力")

        # 3. 比較＆一括エクスポート画面
        response_comp = self.client.get(reverse("demo_comparison", kwargs={"uuid": self.photo.uuid}))
        self.assertEqual(response_comp.status_code, 200)
        self.assertContains(response_comp, "元画像・セグメント・質感レンダリング比較")

        # 4. 3D回転連番画面
        response_rot = self.client.get(reverse("demo_rotation", kwargs={"uuid": self.segmented.uuid}))
        self.assertEqual(response_rot.status_code, 200)
        self.assertContains(response_rot, "3D PBR リアルタイムプレビュー")

    def test_demo_comparison_zip_export(self):
        """素材一括ZIPダウンロードAPIが動作すること"""
        self.client.login(username="staffadmin", password="password123")
        response = self.client.get(reverse("demo_export_comparison", kwargs={"uuid": self.photo.uuid}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
