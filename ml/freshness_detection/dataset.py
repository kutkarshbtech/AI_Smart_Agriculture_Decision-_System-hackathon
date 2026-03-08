"""
Dataset preparation and loading for fruit/vegetable freshness classification.

Expected dataset structure (Kaggle "Food Freshness Dataset" by ULNN Project):
    data/
    ├── Fresh/
    │   ├── Apple/
    │   ├── Banana/
    │   ├── Bell Pepper/
    │   ├── Bitter Gourd/
    │   ├── Capsicum/
    │   ├── Carrot/
    │   ├── Cucumber/
    │   ├── Mango/
    │   ├── Okra/
    │   ├── Orange/
    │   ├── Potato/
    │   ├── Strawberry/
    │   └── Tomato/
    └── Rotten/
        ├── Apple/
        ├── Banana/
        └── ... (same 13 subfolders)

Dataset source: https://www.kaggle.com/datasets/ulnnproject/food-freshness-dataset
~71k images, 6.4 GB, Apache 2.0 license.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import torch
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import datasets, transforms
from PIL import Image


# ── Class definitions ──────────────────────────────────────────────

# The 13 food categories in the ULNN Food Freshness Dataset
FOOD_CATEGORIES = [
    "apple", "banana", "bell_pepper", "bitter_gourd", "capsicum",
    "carrot", "cucumber", "mango", "okra", "orange",
    "potato", "strawberry", "tomato",
]

# Supported fruit/vegetable categories with Hindi names
FRUIT_CLASSES = {
    "fresh_apple":        {"hindi": "ताज़ा सेब",          "freshness": "fresh",  "crop": "apple"},
    "rotten_apple":       {"hindi": "सड़ा सेब",           "freshness": "rotten", "crop": "apple"},
    "fresh_banana":       {"hindi": "ताज़ा केला",         "freshness": "fresh",  "crop": "banana"},
    "rotten_banana":      {"hindi": "सड़ा केला",          "freshness": "rotten", "crop": "banana"},
    "fresh_bell_pepper":  {"hindi": "ताज़ा शिमला मिर्च",  "freshness": "fresh",  "crop": "bell_pepper"},
    "rotten_bell_pepper": {"hindi": "सड़ी शिमला मिर्च",   "freshness": "rotten", "crop": "bell_pepper"},
    "fresh_bitter_gourd": {"hindi": "ताज़ा करेला",        "freshness": "fresh",  "crop": "bitter_gourd"},
    "rotten_bitter_gourd":{"hindi": "सड़ा करेला",         "freshness": "rotten", "crop": "bitter_gourd"},
    "fresh_capsicum":     {"hindi": "ताज़ी शिमला मिर्च",  "freshness": "fresh",  "crop": "capsicum"},
    "rotten_capsicum":    {"hindi": "सड़ी शिमला मिर्च",   "freshness": "rotten", "crop": "capsicum"},
    "fresh_carrot":       {"hindi": "ताज़ा गाजर",        "freshness": "fresh",  "crop": "carrot"},
    "rotten_carrot":      {"hindi": "सड़ी गाजर",         "freshness": "rotten", "crop": "carrot"},
    "fresh_cucumber":     {"hindi": "ताज़ा खीरा",        "freshness": "fresh",  "crop": "cucumber"},
    "rotten_cucumber":    {"hindi": "सड़ा खीरा",         "freshness": "rotten", "crop": "cucumber"},
    "fresh_mango":        {"hindi": "ताज़ा आम",           "freshness": "fresh",  "crop": "mango"},
    "rotten_mango":       {"hindi": "सड़ा आम",            "freshness": "rotten", "crop": "mango"},
    "fresh_okra":         {"hindi": "ताज़ी भिंडी",        "freshness": "fresh",  "crop": "okra"},
    "rotten_okra":        {"hindi": "सड़ी भिंडी",         "freshness": "rotten", "crop": "okra"},
    "fresh_orange":       {"hindi": "ताज़ा संतरा",        "freshness": "fresh",  "crop": "orange"},
    "rotten_orange":      {"hindi": "सड़ा संतरा",         "freshness": "rotten", "crop": "orange"},
    "fresh_potato":       {"hindi": "ताज़ा आलू",          "freshness": "fresh",  "crop": "potato"},
    "rotten_potato":      {"hindi": "सड़ा आलू",           "freshness": "rotten", "crop": "potato"},
    "fresh_strawberry":   {"hindi": "ताज़ी स्ट्रॉबेरी",   "freshness": "fresh",  "crop": "strawberry"},
    "rotten_strawberry":  {"hindi": "सड़ी स्ट्रॉबेरी",    "freshness": "rotten", "crop": "strawberry"},
    "fresh_tomato":       {"hindi": "ताज़ा टमाटर",        "freshness": "fresh",  "crop": "tomato"},
    "rotten_tomato":      {"hindi": "सड़ा टमाटर",         "freshness": "rotten", "crop": "tomato"},
}

# Map index → class name (guaranteed order)
CLASS_NAMES: List[str] = sorted(FRUIT_CLASSES.keys())
NUM_CLASSES: int = len(CLASS_NAMES)
CLASS_TO_IDX: Dict[str, int] = {name: i for i, name in enumerate(CLASS_NAMES)}
IDX_TO_CLASS: Dict[int, str] = {i: name for name, i in CLASS_TO_IDX.items()}

# Mapping from dataset folder name → our internal class name
# The dataset uses "Fresh/Apple", "Rotten/Banana", etc.
_FOLDER_TO_CLASS = {}
for food in FOOD_CATEGORIES:
    # Dataset folder names use title-case with spaces (e.g. "Bell Pepper")
    folder_name = food.replace("_", " ").title()
    _FOLDER_TO_CLASS[("Fresh", folder_name)] = f"fresh_{food}"
    _FOLDER_TO_CLASS[("Rotten", folder_name)] = f"rotten_{food}"


# ── Image transforms ──────────────────────────────────────────────

# MobileNetV2 expects 224×224, ImageNet normalization
IMAGE_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_train_transforms() -> transforms.Compose:
    """
    Training augmentations:
    - Random resized crop (scale variation)
    - Horizontal flip (mirror invariance)
    - Color jitter (lighting robustness)
    - Random rotation (orientation invariance)
    - Random erasing (occlusion robustness)
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.7, 1.0), ratio=(0.8, 1.2)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.1),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(
            brightness=0.3,
            contrast=0.3,
            saturation=0.3,
            hue=0.05,
        ),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        transforms.RandomErasing(p=0.1, scale=(0.02, 0.15)),
    ])


def get_val_transforms() -> transforms.Compose:
    """Validation/inference transforms — deterministic, no augmentation."""
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def get_inference_transforms() -> transforms.Compose:
    """Same as validation — used at inference time."""
    return get_val_transforms()


# ── Folder name normalization ──────────────────────────────────────

# Maps known dataset folder name variations (lowercased) to our internal food keys.
# Handles typos and concatenated naming in the ULNN Food Freshness Dataset.
_FOLDER_NAME_ALIASES: Dict[str, str] = {
    # Standard names
    "apple": "apple",
    "banana": "banana",
    "bell pepper": "bell_pepper",
    "bellpepper": "bell_pepper",
    "bell_pepper": "bell_pepper",
    "bitter gourd": "bitter_gourd",
    "bittergourd": "bitter_gourd",
    "bitter_gourd": "bitter_gourd",
    "bittergroud": "bitter_gourd",   # typo in dataset
    "capsicum": "capsicum",
    "capciscum": "capsicum",         # typo in dataset
    "carrot": "carrot",
    "cucumber": "cucumber",
    "mango": "mango",
    "okra": "okra",
    "okara": "okra",                 # typo in dataset
    "orange": "orange",
    "potato": "potato",
    "strawberry": "strawberry",
    "tomato": "tomato",
}


def _normalize_food_name(raw_name: str) -> Optional[str]:
    """
    Normalize a dataset folder name to our internal food key.
    Handles spaces, underscores, concatenated names, and known typos.
    
    Examples:
        "Apple"       → "apple"
        "Bell Pepper" → "bell_pepper"
        "Bellpepper"  → "bell_pepper"
        "Bittergroud" → "bitter_gourd"
        "Capciscum"   → "capsicum"
        "Okara"       → "okra"
    """
    key = raw_name.strip().lower()
    if key in _FOLDER_NAME_ALIASES:
        return _FOLDER_NAME_ALIASES[key]
    # Try with underscores replaced by spaces and vice versa
    if key.replace("_", " ") in _FOLDER_NAME_ALIASES:
        return _FOLDER_NAME_ALIASES[key.replace("_", " ")]
    if key.replace(" ", "_") in _FOLDER_NAME_ALIASES:
        return _FOLDER_NAME_ALIASES[key.replace(" ", "_")]
    return None


# ── Dataset class ─────────────────────────────────────────────────

class FreshnessDataset(Dataset):
    """
    Custom PyTorch dataset for food freshness images.

    Supports two directory layouts:

    Layout A — ULNN Food Freshness Dataset (Fresh/Rotten top-level):
        root_dir/
        ├── Fresh/
        │   ├── Apple/
        │   ├── Banana/
        │   └── ...
        └── Rotten/
            ├── Apple/
            └── ...

    Layout B — Legacy flat structure (class folders directly):
        root_dir/
        ├── fresh_apple/
        ├── rotten_apple/
        └── ...
    """

    def __init__(self, root_dir: str, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform or get_val_transforms()

        # Collect all image files
        self.samples: List[Tuple[str, int]] = []
        self.class_counts: Dict[str, int] = {}

        # Auto-detect layout
        fresh_dir = self.root_dir / "Fresh"
        rotten_dir = self.root_dir / "Rotten"

        if fresh_dir.exists() and rotten_dir.exists():
            self._load_ulnn_layout(fresh_dir, rotten_dir)
        else:
            self._load_flat_layout()

        print(f"  Loaded {len(self.samples)} images from {root_dir}")
        for cls, count in sorted(self.class_counts.items()):
            if count > 0:
                print(f"    {cls}: {count} images")

    def _load_ulnn_layout(self, fresh_dir: Path, rotten_dir: Path):
        """Load from Fresh/<Food>/ and Rotten/<Food>/ layout."""
        for freshness_label, freshness_dir in [("fresh", fresh_dir), ("rotten", rotten_dir)]:
            if not freshness_dir.exists():
                continue
            for food_folder in sorted(freshness_dir.iterdir()):
                if not food_folder.is_dir():
                    continue

                # Normalize folder name to our internal class name.
                # Dataset uses various conventions:
                #   "Apple", "Bell Pepper"          (space-separated)
                #   "FreshApple", "RottenBellpepper" (prefixed, concatenated)
                raw_name = food_folder.name

                # Strip "Fresh"/"Rotten" prefix if present (e.g. "FreshApple" → "Apple")
                raw_lower = raw_name.lower()
                if raw_lower.startswith("fresh"):
                    raw_name = raw_name[5:]  # strip "Fresh"/"fresh"
                elif raw_lower.startswith("rotten"):
                    raw_name = raw_name[6:]  # strip "Rotten"/"rotten"

                # Normalize to our internal key using a fuzzy lookup table
                # that handles typos in the dataset (Bittergroud, Capciscum, Okara)
                food_key = _normalize_food_name(raw_name)

                if food_key is None:
                    print(f"  Warning: unknown class folder '{food_folder.name}' → could not match, skipping")
                    continue

                class_name = f"{freshness_label}_{food_key}"

                if class_name not in CLASS_TO_IDX:
                    print(f"  Warning: unknown class '{class_name}' from folder '{food_folder.name}', skipping")
                    continue

                images = list(food_folder.glob("*.jpg")) + \
                         list(food_folder.glob("*.jpeg")) + \
                         list(food_folder.glob("*.png")) + \
                         list(food_folder.glob("*.bmp"))

                self.class_counts[class_name] = len(images)
                label_idx = CLASS_TO_IDX[class_name]
                for img_path in images:
                    self.samples.append((str(img_path), label_idx))

    def _load_flat_layout(self):
        """Load from flat fresh_apple/, rotten_apple/ layout."""
        for class_name in CLASS_NAMES:
            class_dir = self.root_dir / class_name
            if not class_dir.exists():
                self.class_counts[class_name] = 0
                continue

            images = list(class_dir.glob("*.jpg")) + \
                     list(class_dir.glob("*.jpeg")) + \
                     list(class_dir.glob("*.png")) + \
                     list(class_dir.glob("*.bmp"))

            self.class_counts[class_name] = len(images)
            for img_path in images:
                self.samples.append((str(img_path), CLASS_TO_IDX[class_name]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]

        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"  Error loading {img_path}: {e}")
            # Return a black image on error
            image = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), (0, 0, 0))

        if self.transform:
            image = self.transform(image)

        return image, label


# ── Data loaders ──────────────────────────────────────────────────

def create_data_loaders(
    data_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    val_split: float = 0.15,
    test_split: float = 0.10,
) -> Tuple[DataLoader, DataLoader, Optional[DataLoader]]:
    """
    Create train, validation, and test data loaders.

    Supports two directory layouts:

    Layout A — ULNN Food Freshness Dataset (auto-split into train/val/test):
        data_dir/
        ├── Fresh/
        │   ├── Apple/
        │   └── ...
        └── Rotten/
            ├── Apple/
            └── ...

    Layout B — Legacy pre-split layout:
        data_dir/
        ├── train/
        │   ├── fresh_apple/
        │   └── ...
        └── test/  (optional)

    Args:
        data_dir: Root data directory
        batch_size: Batch size for data loaders
        num_workers: Number of parallel data loading workers
        val_split: Fraction for validation (used when no separate val/ dir exists)
        test_split: Fraction for test (used when no separate test/ dir exists)

    Returns:
        (train_loader, val_loader, test_loader)
    """
    data_path = Path(data_dir)
    fresh_dir = data_path / "Fresh"
    rotten_dir = data_path / "Rotten"
    train_dir = data_path / "train"
    test_dir = data_path / "test"
    val_dir = data_path / "val"

    # ── Layout A: ULNN Fresh/Rotten structure (single pool, we split it) ──
    if fresh_dir.exists() and rotten_dir.exists():
        print("Detected ULNN Food Freshness Dataset layout (Fresh/ + Rotten/)")
        print("Loading full dataset and splitting into train/val/test...")

        full_dataset = FreshnessDataset(str(data_path), transform=get_train_transforms())

        total = len(full_dataset)
        test_size = int(total * test_split)
        val_size = int(total * val_split)
        train_size = total - val_size - test_size

        train_dataset, val_dataset, test_dataset = random_split(
            full_dataset,
            [train_size, val_size, test_size],
            generator=torch.Generator().manual_seed(42),
        )

        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True,
        )

    # ── Layout B: Legacy train/ + test/ pre-split structure ──
    elif train_dir.exists():
        print("Detected legacy pre-split layout (train/ + test/)")
        print("Loading training data...")
        train_dataset = FreshnessDataset(str(train_dir), transform=get_train_transforms())

        # Validation set
        if val_dir.exists():
            print("Loading validation data from val/ directory...")
            val_dataset = FreshnessDataset(str(val_dir), transform=get_val_transforms())
        else:
            print(f"No val/ directory. Splitting {val_split:.0%} from training data...")
            val_size = int(len(train_dataset) * val_split)
            train_size = len(train_dataset) - val_size
            train_dataset, val_dataset = random_split(
                train_dataset,
                [train_size, val_size],
                generator=torch.Generator().manual_seed(42),
            )

        # Test set
        test_loader = None
        if test_dir.exists():
            print("Loading test data...")
            test_dataset = FreshnessDataset(str(test_dir), transform=get_val_transforms())
            test_loader = DataLoader(
                test_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=True,
            )
    else:
        raise FileNotFoundError(
            f"Could not find dataset in: {data_path}\n"
            f"Expected either:\n"
            f"  (A) ULNN layout:   {data_path}/Fresh/Apple/*.jpg + {data_path}/Rotten/Apple/*.jpg\n"
            f"  (B) Legacy layout: {data_path}/train/fresh_apple/*.jpg"
        )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    print(f"\nDataset summary:")
    print(f"  Train: {len(train_dataset)} images")
    print(f"  Val:   {len(val_dataset)} images")
    if test_loader:
        print(f"  Test:  {len(test_dataset)} images")
    print(f"  Classes: {NUM_CLASSES}")
    print(f"  Batch size: {batch_size}")

    return train_loader, val_loader, test_loader


# ── Dataset scaffold creator ─────────────────────────────────────

def create_dataset_scaffold(data_dir: str) -> None:
    """
    Create the expected directory structure for the ULNN Food Freshness Dataset.
    Users then populate these folders with images.
    """
    data_path = Path(data_dir)

    for freshness in ["Fresh", "Rotten"]:
        for food in FOOD_CATEGORIES:
            folder_name = food.replace("_", " ").title()
            dir_path = data_path / freshness / folder_name
            dir_path.mkdir(parents=True, exist_ok=True)

    print(f"Dataset scaffold created at: {data_path}")
    print(f"Download the dataset from:")
    print(f"  https://www.kaggle.com/datasets/ulnnproject/food-freshness-dataset")
    print(f"Extract so the structure looks like:")
    print(f"  {data_path}/Fresh/Apple/*.jpg")
    print(f"  {data_path}/Fresh/Banana/*.jpg")
    print(f"  {data_path}/Rotten/Apple/*.jpg")
    print(f"  ...")


def save_class_mapping(output_path: str) -> None:
    """Save class name → index mapping as JSON for inference."""
    mapping = {
        "class_to_idx": CLASS_TO_IDX,
        "idx_to_class": {str(k): v for k, v in IDX_TO_CLASS.items()},
        "class_info": FRUIT_CLASSES,
        "num_classes": NUM_CLASSES,
        "image_size": IMAGE_SIZE,
        "imagenet_mean": IMAGENET_MEAN,
        "imagenet_std": IMAGENET_STD,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"Class mapping saved to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dataset preparation")
    parser.add_argument("--action", choices=["scaffold", "verify", "save_mapping"],
                        default="scaffold")
    parser.add_argument("--data_dir", default="data/", help="Dataset root directory")
    parser.add_argument("--output", default="models/class_mapping.json")
    args = parser.parse_args()

    if args.action == "scaffold":
        create_dataset_scaffold(args.data_dir)
    elif args.action == "verify":
        train_loader, val_loader, test_loader = create_data_loaders(args.data_dir, batch_size=4)
        # Test a single batch
        images, labels = next(iter(train_loader))
        print(f"\nSample batch shape: {images.shape}")
        print(f"Sample labels: {[IDX_TO_CLASS[l.item()] for l in labels]}")
    elif args.action == "save_mapping":
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        save_class_mapping(args.output)
