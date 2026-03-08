"""
Export trained freshness model to ONNX and TFLite for deployment.

- ONNX: For backend serving (FastAPI + onnxruntime)
- TFLite: For on-device Android inference (no server needed)

Usage:
    python export_model.py --model models/freshness_v1_best.pth --format onnx
    python export_model.py --model models/freshness_v1_best.pth --format tflite
    python export_model.py --model models/freshness_v1_best.pth --format both
"""

import os
import argparse
from pathlib import Path

import torch
import numpy as np

from dataset import NUM_CLASSES, IMAGE_SIZE, CLASS_NAMES
from model import build_model


def export_onnx(model_path: str, output_path: str = None) -> str:
    """
    Export PyTorch model to ONNX format for server-side inference.

    The ONNX model can be served using onnxruntime for fast CPU/GPU inference.
    """
    if output_path is None:
        output_path = model_path.replace(".pth", ".onnx")

    device = torch.device("cpu")  # Export on CPU

    # Load model
    model = build_model(pretrained=False, freeze_backbone=False)
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Dummy input
    dummy_input = torch.randn(1, 3, IMAGE_SIZE, IMAGE_SIZE)

    # Export
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=13,
        do_constant_folding=True,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={
            "image": {0: "batch_size"},
            "logits": {0: "batch_size"},
        },
    )

    # Verify
    import onnx
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)

    file_size = os.path.getsize(output_path) / 1024 / 1024
    print(f"✓ ONNX model exported to: {output_path}")
    print(f"  Size: {file_size:.1f} MB")

    # Verify with onnxruntime
    try:
        import onnxruntime as ort
        session = ort.InferenceSession(output_path)
        input_name = session.get_inputs()[0].name
        result = session.run(None, {input_name: dummy_input.numpy()})
        print(f"  Output shape: {result[0].shape}")
        print(f"  ✓ ONNX runtime verification passed")
    except ImportError:
        print("  ⚠ onnxruntime not installed — skipping verification")

    return output_path


def export_tflite(model_path: str, output_path: str = None, quantize: bool = True) -> str:
    """
    Export model to TFLite format for Android on-device inference.

    Uses ONNX as intermediate format, then converts to TFLite.
    Optionally applies dynamic range quantization for smaller model.
    """
    if output_path is None:
        output_path = model_path.replace(".pth", ".tflite")

    # Step 1: Export to ONNX first
    onnx_path = model_path.replace(".pth", "_temp.onnx")
    export_onnx(model_path, onnx_path)

    # Step 2: Convert ONNX → TFLite via onnx-tf and tflite
    try:
        import onnx
        from onnx_tf.backend import prepare
        import tensorflow as tf

        # ONNX → TensorFlow SavedModel
        onnx_model = onnx.load(onnx_path)
        tf_rep = prepare(onnx_model)
        saved_model_path = model_path.replace(".pth", "_saved_model")
        tf_rep.export_graph(saved_model_path)

        # TensorFlow → TFLite
        converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_path)

        if quantize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
            print("  Applying float16 quantization for smaller model...")

        tflite_model = converter.convert()

        with open(output_path, "wb") as f:
            f.write(tflite_model)

        file_size = os.path.getsize(output_path) / 1024 / 1024
        print(f"✓ TFLite model exported to: {output_path}")
        print(f"  Size: {file_size:.1f} MB")
        print(f"  Quantized: {quantize}")

        # Cleanup temp files
        os.remove(onnx_path)
        import shutil
        shutil.rmtree(saved_model_path, ignore_errors=True)

    except ImportError as e:
        print(f"⚠ TFLite export requires additional packages: {e}")
        print("  Install: pip install onnx-tf tensorflow")
        print(f"  The ONNX model was saved at: {onnx_path}")
        return onnx_path

    return output_path


def export_torchscript(model_path: str, output_path: str = None) -> str:
    """
    Export to TorchScript for portable PyTorch inference.
    Can be loaded in C++ or Python without model class definition.
    """
    if output_path is None:
        output_path = model_path.replace(".pth", "_scripted.pt")

    device = torch.device("cpu")

    model = build_model(pretrained=False, freeze_backbone=False)
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Trace the model
    dummy_input = torch.randn(1, 3, IMAGE_SIZE, IMAGE_SIZE)
    scripted_model = torch.jit.trace(model, dummy_input)
    scripted_model.save(output_path)

    file_size = os.path.getsize(output_path) / 1024 / 1024
    print(f"✓ TorchScript model exported to: {output_path}")
    print(f"  Size: {file_size:.1f} MB")

    # Verify
    loaded = torch.jit.load(output_path)
    output = loaded(dummy_input)
    print(f"  Output shape: {output.shape}")
    print(f"  ✓ TorchScript verification passed")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Export freshness model")
    parser.add_argument("--model", type=str, default="models/freshness_v1_best.pth",
                        help="Path to trained model checkpoint")
    parser.add_argument("--format", type=str, default="onnx",
                        choices=["onnx", "tflite", "torchscript", "all"],
                        help="Export format")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path (auto-generated if not specified)")
    parser.add_argument("--quantize", action="store_true",
                        help="Apply quantization (TFLite only)")
    args = parser.parse_args()

    if args.format == "onnx" or args.format == "all":
        export_onnx(args.model, args.output)

    if args.format == "tflite" or args.format == "all":
        export_tflite(args.model, args.output, quantize=args.quantize)

    if args.format == "torchscript" or args.format == "all":
        export_torchscript(args.model, args.output)


if __name__ == "__main__":
    main()
