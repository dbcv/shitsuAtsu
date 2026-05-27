
from django.views.decorators.csrf import csrf_exempt

import json

from ollama import chat
from pydantic import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pydantic import BaseModel, Field


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

{
  "material": "材質カテゴリ(metal, plastic, wood, fabric, glass など)",
  "base_color": [0-255のRGB3要素],
  "roughness": 0.00-1.00,
  "metallic": 0.00-1.00
}

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

from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name="dispatch")
class MaterialEstimateAPIView(APIView):

    def get(self, request):
        description = request.data.get("description", "").strip()

        if not description:
            return Response(
                {"error": "description is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = PROMPT_TEMPLATE.format(description=description)

        try:
            response = chat(
                model="nemotron3:33b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options={
                    "temperature": 0.2,
                },
            )

            raw = response.message.content

            parsed = json.loads(raw)

            validated = MaterialParams(**parsed)

            return Response(validated.model_dump())

        except json.JSONDecodeError:
            return Response(
                {
                    "error": "Invalid JSON response from LLM",
                    "raw": raw,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except ValidationError as e:
            return Response(
                {
                    "error": "Schema validation failed",
                    "detail": e.errors(),
                    "raw": raw,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            return Response(
                {
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )