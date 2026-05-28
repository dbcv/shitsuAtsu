# myq/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import uuid
import os
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator

def upload_to_uuid_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'photos/{uuid.uuid4()}{ext}'

class Photo(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(verbose_name='タイトル', max_length=200)
    image = models.ImageField(verbose_name='画像', upload_to=upload_to_uuid_path)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='所有者')
    original_filename = models.CharField(verbose_name='元のファイル名', max_length=255)
    description = models.TextField(verbose_name='説明', blank=True, null=True)
    uploaded_at = models.DateTimeField(verbose_name='アップロード日時', auto_now_add=True)

    def __str__(self):
        return self.title

    def get_image_url(self):
        return reverse('serve_photo', kwargs={'uuid': self.uuid, "ext": "webp"})

    def get_image_url_256(self):
        return reverse('serve_photo', kwargs={'uuid': self.uuid, "width": 256, "ext": "webp"})

    def delete(self, *args, **kwargs):
        storage, path = self.image.storage, self.image.path
        super().delete(*args, **kwargs)
        storage.delete(path)

class SegmentedPhoto(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    original_photo = models.ForeignKey(
        Photo,
        verbose_name='元の画像',
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='segmented_images'
    )
    
    owner = models.ForeignKey(
        User,
        verbose_name='所有者',
        on_delete=models.CASCADE,
    )

    image = models.ImageField(verbose_name='切り抜き画像', upload_to=upload_to_uuid_path)
    created_at = models.DateTimeField(verbose_name='作成日時', auto_now_add=True)
    # Reflection parameters
    diffuse_reflectance = models.FloatField(
        verbose_name='拡散反射率',
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    specular_reflectance = models.FloatField(
        verbose_name='鏡面反射率',
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    albedo = models.CharField(
        verbose_name='アルベド',
        max_length=7,
        default='#FFFFFF',
        help_text='Hex color code, e.g., #FFAA00',
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$')],
    )

    def __str__(self):
        if self.original_photo:
            return f"Segmented from {self.original_photo.title}"
        return f"Segmented photo by {self.owner.username} (Original deleted)"

    def get_image_url(self):
        return reverse('serve_segmented_photo', kwargs={'uuid': self.uuid, "ext": "webp"})

    def get_image_url_256(self):
        return reverse('serve_segmented_photo', kwargs={'uuid': self.uuid, "width": 256, "ext": "webp"})
    
    def get_image_url_64(self):
        return reverse('serve_segmented_photo', kwargs={'uuid': self.uuid, "width": 64, "ext": "webp"})

    def delete(self, *args, **kwargs):
        storage, path = self.image.storage, self.image.path
        super().delete(*args, **kwargs)
        storage.delete(path)

class AutoLoginToken(models.Model):
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    
    token = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.token}"

    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(minutes=10)
        return False
        return timezone.now() > expiration_time

class AccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ユーザー")
    path = models.CharField("アクセスURL", max_length=512)
    method = models.CharField("メソッド", max_length=10)
    ip_address = models.GenericIPAddressField("IPアドレス", null=True, blank=True)
    user_agent = models.TextField("ユーザーエージェント", blank=True)
    referer = models.TextField("リファラ", blank=True)
    timestamp = models.DateTimeField("アクセス時刻", auto_now_add=True)

    class Meta:
        verbose_name = "アクセスログ"
        verbose_name_plural = "アクセスログ一覧"
        ordering = ['-timestamp']

    def __str__(self):
        user = self.user.username if self.user else "匿名"
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {user} {self.method} {self.path}"

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', '男性'),
        ('F', '女性'),
        ('O', 'その他'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    needupdate = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username