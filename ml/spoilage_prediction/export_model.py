"""
Export spoilage prediction model for deployment.

Supports:
    - Joblib (default, for FastAPI backend)
    - ONNX (for optimized CPU/GPU inference)
    - SageMaker packaging (tar.gz for AWS)

Usage:
    python export_model.py                                    # joblib (default)
    python export_model.py --format onnx                      # ONNX export
    python export_model.py --format sagemaker                 # SageMaker tar.gz
    python export_model.py --format all                       # all formats
"""

import os
import json
import shutil
import tarfile
import argparse
from pathlib import Path
from typing import Dict, Any

import numpy as np
import joblib

from dataset import FEATURE_COLUMNS, CROP_NAMES, CROP_TO_IDX, RISK_LEVELS, CROP_PROFILES
from model import SpoilageModel


def export_joblib(model_dir: str = "models", prefix: str = "spoilage_v1", output_dir: str = None):
    """
    Export model in joblib format (already saved during training).
    This just validates and reports file sizes.
    """
    model_path = Path(model_dir)
    files = [
        f"{prefix}_shelf_life.joblib",
        f"{prefix}_probability.joblib",
        f"{prefix}_risk.joblib",
        f"{prefix}_metadata.json",
        f"{prefix}_feature_importance.json",
    ]

    print("── Joblib Export ──")
    total_size = 0
    for f in files:
        p = model_path / f
        if p.exists():
            size = p.stat().st_size
            total_size += size
            print(f"  ✓ {f} ({size / 1024:.1f} KB)")
        else:
            print(f"  ✗ {f} (not found)")

    print(f"  Total: {total_size / 1024 / 1024:.2f} MB")

    if output_dir and output_dir != model_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for f in files:
            src = model_path / f
            if src.exists():
                shutil.copy2(src, out / f)
        print(f"  Copied to {output_dir}/")


def export_sagemaker(
    model_dir: str = "models",
    prefix: str = "spoilage_v1",
    output_dir: str = "models/sagemaker",
):
    """
    Package model for AWS SageMaker deployment.

    Creates a model.tar.gz with:
        - model files (joblib)
        - inference handler
        - metadata
        - requirements
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    model_path = Path(model_dir)

    print("── SageMaker Export ──")

    # Create staging directory
    staging = output_path / "staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    # Copy model files
    for f in [
        f"{prefix}_shelf_life.joblib",
        f"{prefix}_probability.joblib",
        f"{prefix}_risk.joblib",
        f"{prefix}_metadata.json",
    ]:
        src = model_path / f
        if src.exists():
            shutil.copy2(src, staging / f)

    # Create inference handler
    handler_code = '''"""SageMaker inference handler for spoilage prediction."""
import os
import json
import joblib
import numpy as np

FEATURE_COLUMNS = [
    "crop_type_idx", "storage_type", "temperature_c", "humidity_pct",
    "days_since_harvest", "transport_hours", "initial_quality_score",
    "quantity_kg", "damage_sensitivity", "base_shelf_life_days",
    "temp_deviation", "humidity_deviation", "respiration_multiplier",
]

RISK_LEVELS = {0: "low", 1: "medium", 2: "high", 3: "critical"}

PREFIX = "spoilage_v1"


def model_fn(model_dir):
    """Load all three sub-models."""
    models = {
        "shelf_life": joblib.load(os.path.join(model_dir, f"{PREFIX}_shelf_life.joblib")),
        "probability": joblib.load(os.path.join(model_dir, f"{PREFIX}_probability.joblib")),
        "risk": joblib.load(os.path.join(model_dir, f"{PREFIX}_risk.joblib")),
    }
    return models


def input_fn(request_body, content_type="application/json"):
    """Parse input."""
    if content_type == "application/json":
        data = json.loads(request_body)
        features = [data[col] for col in FEATURE_COLUMNS]
        return np.array([features], dtype=np.float32)
    raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, models):
    """Run prediction."""
    shelf_life = float(max(0, models["shelf_life"].predict(input_data)[0]))
    probability = float(np.clip(models["probability"].predict(input_data)[0], 0.01, 0.99))
    risk_level = int(models["risk"].predict(input_data)[0])
    risk_probs = models["risk"].predict_proba(input_data)[0].tolist()

    return {
        "remaining_shelf_life_days": round(shelf_life, 1),
        "spoilage_probability": round(probability, 4),
        "risk_level": risk_level,
        "risk_label": RISK_LEVELS[risk_level],
        "risk_probabilities": {RISK_LEVELS[i]: round(p, 4) for i, p in enumerate(risk_probs)},
    }


def output_fn(prediction, accept="application/json"):
    """Format output."""
    return json.dumps(prediction), accept
'''
    with open(staging / "inference.py", "w") as f:
        f.write(handler_code)

    # Create requirements
    with open(staging / "requirements.txt", "w") as f:
        f.write("xgboost>=2.0.0\njoblib>=1.3.0\nnumpy>=1.26.0\n")

    # Create tar.gz
    tar_path = output_path / "model.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for item in staging.iterdir():
            tar.add(item, arcname=item.name)

    # Cleanup staging
    shutil.rmtree(staging)

    size = tar_path.stat().st_size
    print(f"  ✓ {tar_path} ({size / 1024:.1f} KB)")
    print(f"  Ready for: aws s3 cp {tar_path} s3://your-bucket/models/")


def export_onnx(
    model_dir: str = "models",
    prefix: str = "spoilage_v1",
    output_dir: str = "models",
):
    """
    Export XGBoost models to ONNX format for fast inference.
    
    Requires: pip install onnxmltools skl2onnx
    """
    try:
        import onnxmltools
        from onnxmltools.convert import convert_xgboost
        from onnxconverter_common import FloatTensorType
    except ImportError:
        print("  ONNX export requires: pip install onnxmltools skl2onnx onnxconverter_common")
        print("  Skipping ONNX export.")
        return

    model_path = Path(model_dir)
    output_path = Path(output_dir)

    print("── ONNX Export ──")

    n_features = len(FEATURE_COLUMNS)
    initial_type = [("input", FloatTensorType([None, n_features]))]

    for name in ["shelf_life", "probability", "risk"]:
        src = model_path / f"{prefix}_{name}.joblib"
        if not src.exists():
            print(f"  ✗ {name} model not found")
            continue

        xgb_model = joblib.load(src)
        onnx_model = convert_xgboost(xgb_model, initial_types=initial_type)

        onnx_path = output_path / f"{prefix}_{name}.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())

        size = onnx_path.stat().st_size
        print(f"  ✓ {onnx_path.name} ({size / 1024:.1f} KB)")


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Export spoilage prediction model")
    parser.add_argument("--format", type=str, default="joblib",
                        choices=["joblib", "onnx", "sagemaker", "all"],
                        help="Export format")
    parser.add_argument("--model_dir", type=str, default="models",
                        help="Source model directory")
    parser.add_argument("--prefix", type=str, default="spoilage_v1",
                        help="Model file prefix")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="Output directory (default: same as model_dir)")

    args = parser.parse_args()
    output = args.output_dir or args.model_dir

    print("╔══════════════════════════════════════════╗")
    print("║  SwadeshAI — Model Export                ║")
    print("╚══════════════════════════════════════════╝\n")

    if args.format in ("joblib", "all"):
        export_joblib(args.model_dir, args.prefix, output)

    if args.format in ("onnx", "all"):
        export_onnx(args.model_dir, args.prefix, output)

    if args.format in ("sagemaker", "all"):
        export_sagemaker(args.model_dir, args.prefix, output)

    print("\n✓ Export complete!")


if __name__ == "__main__":
    main()
