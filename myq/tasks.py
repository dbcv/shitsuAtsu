import io
import base64
import zlib

import numpy as np
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from ollama import Client
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView



from .models import Photo, SegmentedPhoto, SegmentedPhoto2


@shared_task
def analyze_material(photo_id):

    photo = Photo.objects.get(id=photo_id)
    print(f"Analyzing material for photo {photo_id}...")

    class MaterialParams(BaseModel):
        material: str
        base_color: list[int] = Field(min_length=3, max_length=3)
        roughness: float = Field(ge=0, le=1)
        metallic: float = Field(ge=0, le=1)


    PROMPT_TEMPLATE = """
    あなたは物理ベースレンダリング（PBR）の専門家です。

    以下の物体の説明文から、材質パラメータを推定してください。

    必ずJSONのみで出力してください。
    余計な文章は一切書かないこと。
    必ず以下を守ること:
    - ``` は絶対に出力しない
    - jsonという単語も出力しない
    - 純粋なJSONのみ出力する

    出力するJSONの形式は以下の通りです:
    {{
    "material": "材質カテゴリ(metal, plastic, wood, fabric, glass など)",
    "base_color": [0-255のRGB3要素],
    "roughness": 0.00-1.00,
    "metallic": 0.00-1.00
    }}

    制約:
    - materialは一般的な材質カテゴリで答えること
    - base_colorは0-255のRGBで必ず3要素で答えること
    - 色空間はsRGB
    - roughnessとmetallicは0.00〜1.00
    - 見た目の特徴から推定する
    - 不明な場合は最も妥当な値を推定する

    物体説明:
    {description}
    """

    
    description = photo.description

    if not description:
        return Response(
            {"error": "description is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    prompt = PROMPT_TEMPLATE.format(description=description)

    client = Client(host=settings.OLLAMA_HOST)

    response = client.chat(
        messages=[
            {
            'role': 'user',
            'content': prompt,
            }
        ],
        model=settings.OLLAMA_MODEL,
        format=MaterialParams.model_json_schema(),
    )

    try:
        entry = MaterialParams.model_validate_json(response.message.content)
    except Exception as e:
        print(f"Error occurred while validating JSON: {e}")

    print(entry)
    photo.roughness = entry.roughness
    photo.metalness = entry.metallic
    photo.albedo = '#%02x%02x%02x' % tuple(entry.base_color)
    photo.save()

def max_square_submatrix(matrix: np.ndarray) -> np.ndarray:
    n, m = matrix.shape
    dp = np.zeros((n, m), dtype=int)

    max_size = 0
    candidates = []

    for i in range(n):
        for j in range(m):
            if matrix[i, j] == 1:
                if i == 0 or j == 0:
                    dp[i, j] = 1
                else:
                    dp[i, j] = min(dp[i-1, j], dp[i, j-1], dp[i-1, j-1]) + 1

                if dp[i, j] > max_size:
                    max_size = dp[i, j]
                    candidates = [(i, j)]
                elif dp[i, j] == max_size:
                    candidates.append((i, j))

    if max_size == 0:
        return np.zeros_like(matrix)

    center = np.array([n/2, m/2])
    best_pos = (0,0)
    best_dist = float("inf")

    for (i, j) in candidates:
        half = max_size / 2
        square_center = np.array([i - half + 0.5, j - half + 0.5])
        dist = np.linalg.norm(square_center - center)
        if dist < best_dist:
            best_dist = dist
            best_pos = (i, j)

    result = np.zeros_like(matrix)
    i, j = best_pos
    for r in range(i - max_size + 1, i + 1):
        for c in range(j - max_size + 1, j + 1):
            result[r, c] = 1

    return result

def crop_with_mask(image: Image.Image, mask: np.ndarray) -> Image.Image:
    """
    マスクが1の部分を含む最小矩形で画像をクロップする
    - image: PIL.Image.Image
    - mask:  2D numpy array (0 or 1), 正方形
    
    return: PIL.Image.Image（クロップ後）
    """
    coords = np.argwhere(mask == 1)
    if coords.size == 0:
        raise ValueError("マスクに1が含まれていません")
    
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    
    h, w = mask.shape
    if (image.width, image.height) != (w, h):
        mask_h, mask_w = mask.shape
        scale_x = image.width / mask_w
        scale_y = image.height / mask_h
        x_min = int(x_min * scale_x)
        x_max = int((x_max + 1) * scale_x)
        y_min = int(y_min * scale_y)
        y_max = int((y_max + 1) * scale_y)

    cropped = image.crop((x_min, y_min, x_max, y_max))
    return cropped


@shared_task
def crop(segmented_id, session_id):

    segmented = get_object_or_404(SegmentedPhoto, uuid=segmented_id)

    if segmented.image:return

    cached = cache.get(f"segment:{session_id}")

    if not cached:
        return
    
    print(cached.get("mask"))

    mask_b64 = cached.get("mask")

    mask_bytes = base64.b64decode(mask_b64)

    packed = np.frombuffer(
        zlib.decompress(mask_bytes),
        dtype=np.uint8
    )

    h, w = cached.get("shape", (0, 0))

    mask = np.unpackbits(
        packed
    )[:h*w].reshape(h, w)

    photo = segmented.original_photo

    image_pil_raw = Image.open(photo.image.path)

    image_pil = ImageOps.exif_transpose(image_pil_raw).convert("RGB")


    cropped = crop_with_mask(
        image_pil,
        max_square_submatrix(mask)
    )

    buffer = io.BytesIO()

    cropped.save(buffer, format="PNG", optimize=True)

    segmented.image.save(
        f"{segmented.uuid}.png",
        ContentFile(buffer.getvalue()),
        save=False
    )

    segmented.save()

    cache.delete(f"segment:{session_id}")