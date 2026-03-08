# Freshness Detection — Computer Vision Model

## Overview
MobileNetV2-based classifier for detecting freshness/ripeness of fruits and vegetables.
Transfer learning from ImageNet, fine-tuned on fruit freshness datasets.

## Classes
- `fresh_apple`, `rotten_apple`
- `fresh_banana`, `rotten_banana`
- `fresh_orange`, `rotten_orange`
- `fresh_mango`, `rotten_mango`
- `fresh_tomato`, `rotten_tomato`
- `fresh_guava`, `rotten_guava`

## Dataset
Uses the "Fruits fresh and rotten for classification" structure from Kaggle.
Place dataset under `data/` with train/test splits.

## Training
```bash
python train.py --data_dir data/ --epochs 25 --batch_size 32
```

## Inference
```bash
python inference.py --image path/to/fruit.jpg --model_path models/freshness_model.pth
```

## Export
```bash
python export_model.py --format onnx     # For backend serving
python export_model.py --format tflite   # For Android on-device
```
