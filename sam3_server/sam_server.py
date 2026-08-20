# sam_server.py

import base64
import io
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import torch
from accelerate import Accelerator
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from sam3.model.sam3_image_processor import Sam3Processor
from sam3.model_builder import build_sam3_image_model
from transformers import Sam3TrackerModel, Sam3TrackerProcessor

SAM3_PROCESSOR: Sam3Processor | None = None
SAM3_TRACKER_MODEL: Sam3TrackerModel | None = None
SAM3_TRACKER_PROCESSOR: Sam3TrackerProcessor | None = None
BASE_DIR = Path(__file__).resolve().parent.parent


def apply_mask_to_cutout(original_image, mask):
    mask_bool = mask > 0

    img_rgba = original_image.convert("RGBA")
    img_np = np.array(img_rgba)

    new_img_np = np.zeros_like(img_np)

    new_img_np[mask_bool] = img_np[mask_bool]

    return Image.fromarray(new_img_np)


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
                    dp[i, j] = min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1]) + 1

                if dp[i, j] > max_size:
                    max_size = dp[i, j]
                    candidates = [(i, j)]
                elif dp[i, j] == max_size:
                    candidates.append((i, j))

    if max_size == 0:
        return np.zeros_like(matrix)

    center = np.array([n / 2, m / 2])
    best_pos = (0, 0)
    best_dist = float("inf")

    for i, j in candidates:
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


def convert_to_optimized_bw(image: Image.Image) -> Image.Image:

    try:
        img = image.convert("RGBA")
        alpha = img.getchannel("A")
        inverted_alpha = Image.eval(alpha, lambda a: 255 - a)

        final_image = inverted_alpha.convert("1", dither=Image.Dither.NONE)

        return final_image

    except FileNotFoundError:
        print("エラー: 入力ファイルが見つかりません")
        return image
    except (OSError, ValueError) as e:
        print(f"エラーが発生しました: {e}")
        return image


@asynccontextmanager
async def lifespan(app: FastAPI):
    global SAM3_PROCESSOR
    global SAM3_TRACKER_MODEL
    global SAM3_TRACKER_PROCESSOR

    print("--- Loading SAM3 Model ---")

    device = Accelerator().device

    print(f"Using device: {device}")

    bpe_path = BASE_DIR / "sam3" / "sam3" / "assets" / "bpe_simple_vocab_16e6.txt.gz"

    sam3_model = build_sam3_image_model(bpe_path=str(bpe_path))

    hf_token = os.environ.get("HF_TOKEN")
    SAM3_PROCESSOR = Sam3Processor(sam3_model)
    SAM3_TRACKER_MODEL = Sam3TrackerModel.from_pretrained("facebook/sam3", token=hf_token).to(device)
    SAM3_TRACKER_PROCESSOR = Sam3TrackerProcessor.from_pretrained("facebook/sam3", token=hf_token)

    print("--- SAM3 Model Loaded Successfully ---")

    yield

    print("--- Shutting Down SAM3 ---")


app = FastAPI(lifespan=lifespan)


@app.post("/segment_text")
async def segment_text(image_path: str = Form(...), description: str = Form(...)):
    try:
        image_pil = Image.open(image_path)
        image_pil = ImageOps.exif_transpose(image_pil).convert("RGB")

        image64, masks, shape = segment_with_text(image_pil, description)

        if masks is None or len(image64) == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "count": 0,
                    "message": "No objects found matching the description.",
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "image64": image64,
                "masks": masks.tolist(),
                "shape": shape,
            },
        )

    except (UnidentifiedImageError, OSError, ValueError, RuntimeError) as e:
        print(f"Error in segment_text: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


def segment_with_text(image_pil, description):
    if SAM3_PROCESSOR is None:
        raise RuntimeError("SAM3 processor is not initialized.")

    with torch.autocast("cuda", dtype=torch.bfloat16):
        inference_state = SAM3_PROCESSOR.set_image(image_pil)
        output = SAM3_PROCESSOR.set_text_prompt(
            state=inference_state, prompt=description
        )

    image64 = []

    masks = output.get("masks", [])

    m = masks
    print(m)
    print("type(output['masks']):", type(m))

    if hasattr(m, "shape"):
        print("output['masks'].shape:", m.shape, "dtype:", getattr(m, "dtype", None))

    if (
        masks is None
        or len(masks) == 0
        or (hasattr(masks, "shape") and (masks.shape[0] == 0 or masks.numel() == 0))
    ):
        return [], None, (image_pil.height, image_pil.width)

    mask_np = masks[0].squeeze().detach().cpu().numpy()
    if mask_np.size == 0 or not np.any(mask_np):
        return [], None, (image_pil.height, image_pil.width)

    masks = mask_np.astype(np.uint8)

    buffered = io.BytesIO()
    image = apply_mask_to_cutout(image_pil, masks)
    print("Pattern2 masks shape:", masks.shape, "dtype:", masks.dtype)
    shape = masks.shape
    image = convert_to_optimized_bw(image)
    image.save(buffered, format="PNG", optimize=True)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    image64.append(img_str)

    return image64, masks, shape


@app.post("/segment_points")
async def segment_points(
    image_path: str = Form(...), ppoints: str = Form(...), npoints: str = Form(...)
):
    try:
        image_pil = Image.open(image_path)
        image_pil = ImageOps.exif_transpose(image_pil).convert("RGB")

        ppoints = json.loads(ppoints)
        npoints = json.loads(npoints)

        image64, masks, shape = segment_with_points(image_pil, ppoints, npoints)

        if masks is None or len(image64) == 0:
            return JSONResponse(
                status_code=200,
                content={"success": False, "count": 0, "message": "No objects found."},
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "image64": image64,
                "masks": masks.tolist(),
                "shape": shape,
            },
        )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        RuntimeError,
    ) as e:
        print(f"Error in segment_points: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


def segment_with_points(image_pil, ppoints, npoints):
    if SAM3_TRACKER_PROCESSOR is None or SAM3_TRACKER_MODEL is None:
        raise RuntimeError("SAM3 tracker model or processor is not initialized.")

    input_point = []
    input_label = []
    for p in ppoints:
        input_point.append([p["x"], p["y"]])
        input_label.append(1)
    for p in npoints:
        input_point.append([p["x"], p["y"]])
        input_label.append(0)

    input_point = np.array([[input_point]])
    input_label = np.array([[input_label]])

    inputs = SAM3_TRACKER_PROCESSOR(
        image_pil,
        input_points=input_point,
        input_labels=input_label,
        return_tensors="pt",
    ).to(SAM3_TRACKER_MODEL.device)

    with torch.no_grad():
        outputs = SAM3_TRACKER_MODEL(**inputs, multimask_output=False)

    image64 = []

    masks = SAM3_TRACKER_PROCESSOR.post_process_masks(
        outputs.pred_masks.cpu(), inputs["original_sizes"]
    )[0]

    m = masks
    print(m)
    print("type(output['masks']):", type(m))

    if hasattr(m, "shape"):
        print("output['masks'].shape:", m.shape, "dtype:", getattr(m, "dtype", None))

    if (
        masks is None
        or len(masks) == 0
        or (hasattr(masks, "shape") and (masks.shape[0] == 0 or masks.numel() == 0))
    ):
        return [], None, (image_pil.height, image_pil.width)

    mask_np = masks[0].squeeze().detach().cpu().numpy()
    if mask_np.size == 0 or not np.any(mask_np):
        return [], None, (image_pil.height, image_pil.width)

    masks = mask_np.astype(np.uint8)

    buffered = io.BytesIO()
    image = apply_mask_to_cutout(image_pil, masks)
    print("Pattern2 masks shape:", masks.shape, "dtype:", masks.dtype)
    shape = masks.shape
    image = convert_to_optimized_bw(image)
    image.save(buffered, format="PNG", optimize=True)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    image64.append(img_str)

    return image64, masks, shape


@app.get("/")
async def root():
    return {"message": "SAM3 API is running"}
