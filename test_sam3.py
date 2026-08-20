#!/usr/bin/env python3
"""SAM3 ポイントマーカーテストスクリプト

Docker ではなくローカル環境（venv）から直接実行可能な SAM3 テストプログラムです。
1. 画像を読み込む
2. 範囲内マーカー（ポジティブ座標）と範囲外マーカー（ネガティブ座標）を SAM3 に入力
3. 対象物を切り抜いた透過 PNG 画像を出力
4. 2値（白黒）のマスク PNG 画像を出力
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from PIL import Image, ImageOps, UnidentifiedImageError
from transformers import Sam3TrackerModel, Sam3TrackerProcessor


def load_image(image_path: Path) -> Image.Image:
    """画像を読み込み、EXIF 回転を補正して RGB 形式で返す"""
    if not image_path.exists():
        raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image).convert("RGB")
    return image


def parse_points(points_str: str) -> List[Tuple[float, float]]:
    """'x1,y1 x2,y2' 形式または 'x1,y1,x2,y2' 形式の文字列を座標タプルのリストに変換"""
    if not points_str.strip():
        return []
    result = []
    # スペースまたはカンマ区切りに対応
    raw_tokens = points_str.replace(";", " ").replace("/", " ").split()
    for token in raw_tokens:
        parts = [p.strip() for p in token.split(",") if p.strip()]
        if len(parts) == 2:
            result.append((float(parts[0]), float(parts[1])))
    return result


def apply_mask_to_cutout(original_image: Image.Image, mask: np.ndarray) -> Image.Image:
    """元画像にマスク（1: 抽出領域, 0: 背景）を適用して背景を透明化した RGBA 画像を生成"""
    mask_bool = mask > 0
    img_rgba = original_image.convert("RGBA")
    img_np = np.array(img_rgba)

    # 抽出領域以外を透明 (alpha = 0) に設定
    output_np = np.zeros_like(img_np)
    output_np[mask_bool] = img_np[mask_bool]

    return Image.fromarray(output_np, mode="RGBA")


def create_binary_mask_image(mask: np.ndarray) -> Image.Image:
    """0/1 またはブール値のマスク配列から 2値（黒:0, 白:255）の PNG 画像を生成"""
    binary_mask = (mask > 0).astype(np.uint8) * 255
    return Image.fromarray(binary_mask, mode="L")


def run_sam3_segmentation(
    image: Image.Image,
    positive_points: List[Tuple[float, float]],
    negative_points: List[Tuple[float, float]],
    model_id: str = "facebook/sam3",
    device: str | None = None,
) -> Tuple[np.ndarray, Image.Image, Image.Image]:
    """SAM3 を用いて指定座標からマスクおよび切り抜き画像を生成

    Returns:
        (mask_np, cutout_image, binary_mask_image)
    """
    if not positive_points and not negative_points:
        raise ValueError("少なくとも1つの座標（範囲内または範囲外）を指定してください。")

    # デバイス決定
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] 使用デバイス: {device}")

    # モデル & プロセッサの読み込み
    print(f"[*] SAM3 モデル読み込み中 ({model_id})...")
    processor = Sam3TrackerProcessor.from_pretrained(model_id)
    model = Sam3TrackerModel.from_pretrained(model_id).to(device)
    model.eval()

    # ポイントとラベルのフォーマット作成
    # label: 1 = ポジティブ（範囲内）, 0 = ネガティブ（範囲外）
    input_points_list = []
    input_labels_list = []

    for x, y in positive_points:
        input_points_list.append([x, y])
        input_labels_list.append(1)

    for x, y in negative_points:
        input_points_list.append([x, y])
        input_labels_list.append(0)

    # SAM3 Tracker が要求する形状: (batch_size, num_frames, num_points, 2)
    input_points_np = np.array([[input_points_list]])
    input_labels_np = np.array([[input_labels_list]])

    print(f"[*] 範囲内マーカー (Positive, label=1): {positive_points}")
    print(f"[*] 範囲外マーカー (Negative, label=0): {negative_points}")

    # 前処理
    inputs = processor(
        image,
        input_points=input_points_np,
        input_labels=input_labels_np,
        return_tensors="pt",
    ).to(device)

    # 推論実行
    print("[*] SAM3 推論中...")
    with torch.no_grad():
        outputs = model(**inputs, multimask_output=False)

    # 後処理（元画像サイズに合わせたマスクの復元）
    masks = processor.post_process_masks(
        outputs.pred_masks.cpu(), inputs["original_sizes"]
    )[0]

    if masks is None or len(masks) == 0:
        raise RuntimeError("マスクの生成に失敗しました（空のマスクが返されました）。")

    mask_np = masks[0].squeeze().detach().cpu().numpy()
    if mask_np.ndim != 2:
        raise RuntimeError(f"不正なマスク形状です: {mask_np.shape}")

    # 2値マスク (0 or 1) に変換
    binary_mask_np = (mask_np > 0).astype(np.uint8)

    # 透過切り抜き画像 & 2値マスク画像の作成
    cutout_img = apply_mask_to_cutout(image, binary_mask_np)
    mask_img = create_binary_mask_image(binary_mask_np)

    return binary_mask_np, cutout_img, mask_img


def find_default_sample_image() -> Path | None:
    """プロジェクト内の media/photos ディレクトリからテスト用画像を1枚探索"""
    base_dir = Path(__file__).resolve().parent
    photos_dir = base_dir / "media" / "photos"
    if photos_dir.exists():
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            found = sorted(photos_dir.glob(ext))
            if found:
                return found[0]
    return None


def main():
    parser = argparse.ArgumentParser(
        description="SAM3 を使用したポイント指定画像切り抜き & 2値マスク生成テストプログラム"
    )
    parser.add_argument(
        "--image",
        "-i",
        type=str,
        default=None,
        help="入力画像パス (省略時は media/photos/ から自動検出)",
    )
    parser.add_argument(
        "--pos",
        "-p",
        type=str,
        default=None,
        help="範囲内マーカー座標 (例: '250,300 400,350')",
    )
    parser.add_argument(
        "--neg",
        "-n",
        type=str,
        default="",
        help="範囲外マーカー座標 (例: '50,50 100,200')",
    )
    parser.add_argument(
        "--out-mask",
        "-om",
        type=str,
        default="output_mask.png",
        help="2値マスク画像 PNG 出力先パス (デフォルト: output_mask.png)",
    )
    parser.add_argument(
        "--out-cutout",
        "-oc",
        type=str,
        default="output_cutout.png",
        help="切り抜き透過画像 PNG 出力先パス (デフォルト: output_cutout.png)",
    )
    parser.add_argument(
        "--device",
        "-d",
        type=str,
        default=None,
        help="実行デバイス ('cuda' または 'cpu', 省略時は自動検出)",
    )

    args = parser.parse_args()

    # 画像パスの解決
    if args.image:
        image_path = Path(args.image)
    else:
        sample = find_default_sample_image()
        if sample:
            image_path = sample
            print(f"[*] 画像が指定されていないため、サンプル画像を使用します: {image_path}")
        else:
            print("[!] 画像ファイルが見つかりません。--image で画像パスを指定してください。")
            sys.exit(1)

    try:
        image = load_image(image_path)
        print(f"[*] 画像読み込み完了: {image_path} (サイズ: {image.width}x{image.height})")
    except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
        print(f"[!] 画像の読み込みに失敗しました: {e}")
        sys.exit(1)

    # 座標の解決 (指定がない場合は画像中心をデフォルトのポジティブ座標にする)
    if args.pos:
        positive_points = parse_points(args.pos)
    else:
        center_x = image.width / 2.0
        center_y = image.height / 2.0
        positive_points = [(center_x, center_y)]
        print(f"[*] 範囲内マーカー未指定のため、画像中心を使用します: ({center_x:.1f}, {center_y:.1f})")

    negative_points = parse_points(args.neg) if args.neg else []

    # SAM3 セグメンテーション実行
    try:
        mask_np, cutout_img, mask_img = run_sam3_segmentation(
            image=image,
            positive_points=positive_points,
            negative_points=negative_points,
            device=args.device,
        )
    except Exception as e:
        print(f"[!] SAM3 セグメンテーション実行中にエラーが発生しました: {e}")
        sys.exit(1)

    # 出力保存
    out_mask_path = Path(args.out_mask)
    out_cutout_path = Path(args.out_cutout)

    mask_img.save(out_mask_path, format="PNG")
    print(f"[✓] 2値マスク画像を保存しました: {out_mask_path.resolve()} (モード: {mask_img.mode}, サイズ: {mask_img.size})")

    cutout_img.save(out_cutout_path, format="PNG")
    print(f"[✓] 切り抜き透過画像を保存しました: {out_cutout_path.resolve()} (モード: {cutout_img.mode}, サイズ: {cutout_img.size})")

    foreground_pixels = int(np.sum(mask_np > 0))
    total_pixels = mask_np.size
    print(f"[*] マスク統計: 抽出領域 {foreground_pixels} px / 全体 {total_pixels} px ({foreground_pixels / total_pixels * 100:.2f}%)")
    print("[✓] 処理が正常に完了しました。")


if __name__ == "__main__":
    main()
