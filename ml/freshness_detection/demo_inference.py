"""
Demo inference script — test the full freshness detection pipeline
without needing a Kaggle-trained model or real dataset.

What this does:
    1. Creates a MobileNetV2 model with ImageNet-pretrained backbone
       and saves a "demo" checkpoint (classifier head has random weights)
    2. Generates a synthetic fruit-like test image using PIL
    3. Downloads a real sample image from the web (optional, if internet available)
    4. Runs the inference engine on the sample image
    5. Prints the full result including Hindi recommendations

Usage:
    cd ml/freshness_detection
    pip install torch torchvision Pillow numpy
    python demo_inference.py
    python demo_inference.py --use_real_image       # tries to fetch a real fruit photo
    python demo_inference.py --image your_photo.jpg  # use your own image
"""

import os
import sys
import json
import argparse
from pathlib import Path

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Add parent to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset import CLASS_NAMES, NUM_CLASSES, FRUIT_CLASSES, IDX_TO_CLASS
from model import build_model
from inference import FreshnessDetector


def create_demo_checkpoint(output_dir: str = "models") -> str:
    """
    Create a demo model checkpoint using ImageNet-pretrained MobileNetV2.
    The classifier head will have random (untrained) weights, so predictions
    won't be accurate — but the full pipeline will run end-to-end.

    Returns:
        Path to saved checkpoint
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    checkpoint_path = output_path / "freshness_demo_best.pth"

    if checkpoint_path.exists():
        # Verify checkpoint has the right number of classes
        try:
            existing = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
            if existing.get("num_classes") != NUM_CLASSES:
                print(f"[INFO] Stale checkpoint ({existing.get('num_classes')} classes vs {NUM_CLASSES}). Rebuilding...")
                checkpoint_path.unlink()
            else:
                print(f"[OK] Demo checkpoint already exists: {checkpoint_path}")
                return str(checkpoint_path)
        except Exception:
            checkpoint_path.unlink(missing_ok=True)

    print("Creating demo model checkpoint (ImageNet-pretrained backbone + random classifier)...")
    model = build_model(pretrained=True, freeze_backbone=False)

    checkpoint = {
        "epoch": 0,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": {},
        "val_acc": 0.0,
        "num_classes": NUM_CLASSES,
        "class_names": CLASS_NAMES,
        "note": "DEMO ONLY — classifier head is untrained. Train on real data for accurate predictions.",
    }

    torch.save(checkpoint, checkpoint_path)
    print(f"[OK] Saved demo checkpoint: {checkpoint_path}")
    print(f"     Model params: {sum(p.numel() for p in model.parameters()):,}")

    # Also save class mapping
    class_mapping = {
        "idx_to_class": {str(k): v for k, v in IDX_TO_CLASS.items()},
        "class_to_idx": {v: k for k, v in IDX_TO_CLASS.items()},
        "fruit_classes": FRUIT_CLASSES,
    }
    mapping_path = output_path / "class_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(class_mapping, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved class mapping: {mapping_path}")

    return str(checkpoint_path)


def create_synthetic_fruit_image(output_path: str = "samples/sample_tomato.jpg") -> str:
    """
    Generate a synthetic fruit-like test image using PIL.
    Creates a realistic-ish tomato image (red circle with green top on white bg).

    Returns:
        Path to the generated image
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists():
        print(f"[OK] Sample image already exists: {out}")
        return str(out)

    print(f"Generating synthetic test image: {out}")

    # Create a 300x300 image with a gradient background
    img = Image.new("RGB", (300, 300), (245, 240, 230))
    draw = ImageDraw.Draw(img)

    # Draw a tomato-like shape (red ellipse)
    draw.ellipse([60, 70, 240, 250], fill=(220, 40, 30), outline=(180, 30, 20))

    # Add some shading (darker red on bottom-right)
    draw.ellipse([140, 140, 235, 245], fill=(190, 35, 25))

    # Highlight on top-left
    draw.ellipse([85, 85, 140, 140], fill=(240, 70, 50))

    # Stem (green)
    draw.polygon([(130, 75), (150, 40), (170, 75)], fill=(50, 140, 40))
    draw.polygon([(140, 70), (160, 50), (155, 75)], fill=(60, 160, 50))

    # Small leaf shape
    draw.ellipse([155, 40, 195, 60], fill=(40, 130, 35))

    # Apply slight blur for realism
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    img.save(str(out), "JPEG", quality=90)
    print(f"[OK] Saved synthetic image: {out}")
    return str(out)


def create_sample_rotten_image(output_path: str = "samples/sample_rotten_banana.jpg") -> str:
    """Generate a synthetic rotten banana image."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists():
        print(f"[OK] Sample image already exists: {out}")
        return str(out)

    print(f"Generating synthetic rotten banana image: {out}")

    img = Image.new("RGB", (300, 300), (240, 235, 225))
    draw = ImageDraw.Draw(img)

    # Banana shape (dark brownish yellow = rotten)
    draw.ellipse([40, 100, 260, 200], fill=(130, 110, 30), outline=(90, 70, 20))
    # Dark spots
    for x, y in [(100, 140), (160, 155), (200, 135), (130, 165), (180, 145)]:
        r = np.random.randint(5, 15)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(60, 40, 10))

    # Stem
    draw.rectangle([45, 140, 55, 170], fill=(80, 60, 20))

    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    img.save(str(out), "JPEG", quality=90)
    print(f"[OK] Saved synthetic rotten image: {out}")
    return str(out)


def download_real_sample(output_path: str = "samples/real_apple.jpg") -> str:
    """
    Try to download a real fruit image from the web for testing.
    Falls back to synthetic if download fails.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists():
        print(f"[OK] Real sample already exists: {out}")
        return str(out)

    try:
        import urllib.request
        # Unsplash source for a free apple image (small size)
        url = "https://images.unsplash.com/photo-1568702846914-96b305d2uj68?w=300&h=300&fit=crop"
        print(f"Attempting to download a real fruit image...")
        urllib.request.urlretrieve(url, str(out))
        print(f"[OK] Downloaded real sample: {out}")
        return str(out)
    except Exception as e:
        print(f"[WARN] Could not download real image: {e}")
        print("       Using synthetic image instead.")
        return create_synthetic_fruit_image()


def run_inference(image_path: str, model_path: str, device: str = None):
    """Run the full inference pipeline and print results."""
    print(f"\n{'='*60}")
    print(f"  LOADING MODEL")
    print(f"{'='*60}")

    detector = FreshnessDetector(
        model_path=model_path,
        device=device,
        confidence_threshold=0.5,
    )

    print(f"\n{'='*60}")
    print(f"  RUNNING INFERENCE")
    print(f"{'='*60}")
    print(f"  Image: {image_path}")

    result = detector.predict(image_path)

    # ── Print results ─────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  FRESHNESS DETECTION RESULT")
    print(f"{'='*60}")
    print(f"  Image:      {image_path}")
    print(f"  Crop:       {result['crop_type']}")
    print(f"  Hindi:      {result['hindi_label']}")
    print()
    status_emoji = "🟢 FRESH" if result["freshness_status"] == "fresh" else "🔴 ROTTEN"
    print(f"  Status:     {status_emoji}")
    print(f"  Confidence: {result['confidence']*100:.1f}%")
    print(f"  Confident:  {'Yes' if result['is_confident'] else 'No (below threshold)'}")
    print(f"  Grade:      {result['quality_grade'].upper()}")
    print(f"  Score:      {result['freshness_score']}/100")
    print(f"  Time:       {result['inference_time_ms']:.1f}ms")

    print(f"\n  ── Recommendations ──")
    rec = result["recommendations"]
    print(f"  Action:     {rec['action']}")
    print(f"  Urgency:    {rec['urgency'].upper()}")
    print(f"  EN: {rec['english']}")
    print(f"  HI: {rec['hindi']}")
    print(f"  Storage EN: {rec.get('storage_advice_en', 'N/A')}")
    print(f"  Storage HI: {rec.get('storage_advice_hi', 'N/A')}")

    print(f"\n  ── Top Predictions ──")
    for i, pred in enumerate(result["top_predictions"], 1):
        bar = "█" * int(pred["confidence"] * 30)
        print(f"  {i}. {pred['class']:20s} {pred['confidence']*100:5.1f}% {bar}  {pred['hindi']}")

    print(f"\n{'='*60}")
    print(f"  NOTE: This is a DEMO with untrained classifier head.")
    print(f"  Predictions are random. Train on real data for accuracy:")
    print(f"    python train.py --data_dir data/ --epochs 25 --batch_size 32")
    print(f"{'='*60}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Demo: test freshness detection pipeline end-to-end"
    )
    parser.add_argument(
        "--image", type=str, default=None,
        help="Path to your own fruit image (skip synthetic generation)"
    )
    parser.add_argument(
        "--use_real_image", action="store_true",
        help="Try downloading a real fruit photo from the web"
    )
    parser.add_argument(
        "--device", type=str, default=None, choices=["cuda", "cpu"],
        help="Force device (default: auto-detect)"
    )
    parser.add_argument(
        "--all_samples", action="store_true",
        help="Run inference on all synthetic sample images"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  SwadeshAI — Freshness Detection Demo")
    print("  MobileNetV2 Transfer Learning Pipeline")
    print("=" * 60)

    # Step 1: Create demo checkpoint
    model_path = create_demo_checkpoint()
    print()

    # Step 2: Get test image(s)
    if args.image:
        if not os.path.exists(args.image):
            print(f"[ERROR] Image not found: {args.image}")
            sys.exit(1)
        images = [args.image]
    elif args.use_real_image:
        images = [download_real_sample()]
    elif args.all_samples:
        images = [
            create_synthetic_fruit_image(),
            create_sample_rotten_image(),
        ]
    else:
        images = [create_synthetic_fruit_image()]

    # Step 3: Run inference on each image
    for img_path in images:
        run_inference(img_path, model_path, device=args.device)


if __name__ == "__main__":
    main()
