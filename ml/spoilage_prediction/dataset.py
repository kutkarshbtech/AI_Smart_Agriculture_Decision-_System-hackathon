"""
Synthetic dataset generation for spoilage prediction model.

Generates realistic training data based on agricultural science:
    - Q10 temperature rule (enzymatic activity doubles per 10°C)
    - Humidity impact on microbial growth and moisture loss
    - Transport mechanical damage
    - Crop-specific shelf-life profiles for 16 Indian crops
    - Indian seasonal weather patterns

Features:
    - crop_type (categorical, one-hot encoded)
    - storage_type (0=ambient, 1=cold)
    - temperature_c (current storage temp)
    - humidity_pct (current relative humidity)
    - days_since_harvest (days elapsed)
    - transport_hours (hours in transit)
    - initial_quality_score (0-100, harvest quality)
    - quantity_kg (batch size)

Targets:
    - remaining_shelf_life_days (regression)
    - spoilage_probability (regression, 0-1)
    - risk_level (classification: 0=low, 1=medium, 2=high, 3=critical)

Usage:
    python dataset.py                          # generate default dataset
    python dataset.py --samples 100000         # larger dataset
    python dataset.py --output data/custom.csv # custom output path
"""

import os
import math
import json
import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd


# ── Crop profiles (from agricultural science literature) ─────────────

CROP_PROFILES = {
    "tomato": {
        "ambient_days": 7,
        "cold_days": 21,
        "optimal_temp": (10, 15),
        "optimal_humidity": (85, 95),
        "category": "vegetable",
        "hindi": "टमाटर",
        "respiration_rate": "high",       # ethylene-producing climacteric fruit
        "damage_sensitivity": 0.7,         # 0-1, mechanical damage sensitivity
    },
    "potato": {
        "ambient_days": 30,
        "cold_days": 120,
        "optimal_temp": (4, 8),
        "optimal_humidity": (90, 95),
        "category": "vegetable",
        "hindi": "आलू",
        "respiration_rate": "low",
        "damage_sensitivity": 0.3,
    },
    "onion": {
        "ambient_days": 30,
        "cold_days": 180,
        "optimal_temp": (0, 4),
        "optimal_humidity": (65, 70),
        "category": "vegetable",
        "hindi": "प्याज",
        "respiration_rate": "low",
        "damage_sensitivity": 0.4,
    },
    "banana": {
        "ambient_days": 5,
        "cold_days": 14,
        "optimal_temp": (13, 15),
        "optimal_humidity": (85, 95),
        "category": "fruit",
        "hindi": "केला",
        "respiration_rate": "very_high",
        "damage_sensitivity": 0.9,
    },
    "mango": {
        "ambient_days": 5,
        "cold_days": 21,
        "optimal_temp": (10, 13),
        "optimal_humidity": (85, 90),
        "category": "fruit",
        "hindi": "आम",
        "respiration_rate": "high",
        "damage_sensitivity": 0.6,
    },
    "apple": {
        "ambient_days": 14,
        "cold_days": 120,
        "optimal_temp": (0, 4),
        "optimal_humidity": (90, 95),
        "category": "fruit",
        "hindi": "सेब",
        "respiration_rate": "low",
        "damage_sensitivity": 0.5,
    },
    "rice": {
        "ambient_days": 365,
        "cold_days": 730,
        "optimal_temp": (15, 20),
        "optimal_humidity": (60, 70),
        "category": "grain",
        "hindi": "चावल",
        "respiration_rate": "very_low",
        "damage_sensitivity": 0.1,
    },
    "wheat": {
        "ambient_days": 180,
        "cold_days": 365,
        "optimal_temp": (15, 20),
        "optimal_humidity": (60, 65),
        "category": "grain",
        "hindi": "गेहूं",
        "respiration_rate": "very_low",
        "damage_sensitivity": 0.1,
    },
    "cauliflower": {
        "ambient_days": 4,
        "cold_days": 21,
        "optimal_temp": (0, 2),
        "optimal_humidity": (95, 98),
        "category": "vegetable",
        "hindi": "फूलगोभी",
        "respiration_rate": "high",
        "damage_sensitivity": 0.8,
    },
    "spinach": {
        "ambient_days": 2,
        "cold_days": 10,
        "optimal_temp": (0, 2),
        "optimal_humidity": (95, 100),
        "category": "leafy_green",
        "hindi": "पालक",
        "respiration_rate": "very_high",
        "damage_sensitivity": 0.95,
    },
    "okra": {
        "ambient_days": 3,
        "cold_days": 10,
        "optimal_temp": (7, 10),
        "optimal_humidity": (90, 95),
        "category": "vegetable",
        "hindi": "भिंडी",
        "respiration_rate": "high",
        "damage_sensitivity": 0.7,
    },
    "brinjal": {
        "ambient_days": 5,
        "cold_days": 14,
        "optimal_temp": (10, 12),
        "optimal_humidity": (90, 95),
        "category": "vegetable",
        "hindi": "बैंगन",
        "respiration_rate": "medium",
        "damage_sensitivity": 0.6,
    },
    "grape": {
        "ambient_days": 3,
        "cold_days": 42,
        "optimal_temp": (-1, 0),
        "optimal_humidity": (90, 95),
        "category": "fruit",
        "hindi": "अंगूर",
        "respiration_rate": "low",
        "damage_sensitivity": 0.85,
    },
    "guava": {
        "ambient_days": 5,
        "cold_days": 21,
        "optimal_temp": (8, 10),
        "optimal_humidity": (85, 95),
        "category": "fruit",
        "hindi": "अमरूद",
        "respiration_rate": "high",
        "damage_sensitivity": 0.6,
    },
    "carrot": {
        "ambient_days": 7,
        "cold_days": 120,
        "optimal_temp": (0, 2),
        "optimal_humidity": (95, 100),
        "category": "vegetable",
        "hindi": "गाजर",
        "respiration_rate": "low",
        "damage_sensitivity": 0.4,
    },
    "capsicum": {
        "ambient_days": 5,
        "cold_days": 21,
        "optimal_temp": (7, 10),
        "optimal_humidity": (90, 95),
        "category": "vegetable",
        "hindi": "शिमला मिर्च",
        "respiration_rate": "medium",
        "damage_sensitivity": 0.5,
    },
}

CROP_NAMES = sorted(CROP_PROFILES.keys())
NUM_CROPS = len(CROP_NAMES)
CROP_TO_IDX = {name: idx for idx, name in enumerate(CROP_NAMES)}
IDX_TO_CROP = {idx: name for name, idx in CROP_TO_IDX.items()}

RISK_LEVELS = {0: "low", 1: "medium", 2: "high", 3: "critical"}
RISK_TO_IDX = {v: k for k, v in RISK_LEVELS.items()}

# Respiration rate multipliers (higher = faster spoilage baseline)
RESPIRATION_MULTIPLIER = {
    "very_low": 0.8,
    "low": 0.9,
    "medium": 1.0,
    "high": 1.2,
    "very_high": 1.4,
}

# ── Indian seasonal temperature distributions ───────────────────────

INDIAN_SEASONS = {
    "summer":  {"temp_mean": 38, "temp_std": 5, "humidity_mean": 45, "humidity_std": 15},
    "monsoon": {"temp_mean": 30, "temp_std": 4, "humidity_mean": 85, "humidity_std": 10},
    "winter":  {"temp_mean": 18, "temp_std": 6, "humidity_mean": 60, "humidity_std": 15},
    "autumn":  {"temp_mean": 28, "temp_std": 5, "humidity_mean": 55, "humidity_std": 15},
}


# ── Feature names ───────────────────────────────────────────────────

FEATURE_COLUMNS = [
    "crop_type_idx",
    "storage_type",           # 0=ambient, 1=cold
    "temperature_c",
    "humidity_pct",
    "days_since_harvest",
    "transport_hours",
    "initial_quality_score",  # 0-100
    "quantity_kg",
    "damage_sensitivity",
    "base_shelf_life_days",
    "temp_deviation",         # degrees from optimal range
    "humidity_deviation",     # percentage points from optimal range
    "respiration_multiplier",
]

TARGET_COLUMNS = [
    "remaining_shelf_life_days",
    "spoilage_probability",
    "risk_level",
]


def _temperature_factor(current_temp: float, optimal_min: float, optimal_max: float) -> float:
    """Q10 temperature degradation factor."""
    if optimal_min <= current_temp <= optimal_max:
        return 1.0
    if current_temp > optimal_max:
        delta = current_temp - optimal_max
        return min(2 ** (delta / 10), 5.0)
    if current_temp < optimal_min and current_temp >= 0:
        delta = optimal_min - current_temp
        return 1.0 + (delta * 0.05)
    if current_temp < 0:
        return 3.0
    return 1.0


def _humidity_factor(current_humidity: float, optimal_min: float, optimal_max: float) -> float:
    """Humidity degradation factor."""
    if optimal_min <= current_humidity <= optimal_max:
        return 1.0
    if current_humidity < optimal_min:
        delta = optimal_min - current_humidity
        return 1.0 + (delta * 0.02)
    if current_humidity > optimal_max:
        delta = current_humidity - optimal_max
        return 1.0 + (delta * 0.03)
    return 1.0


def _spoilage_probability(days_elapsed: float, adjusted_shelf_life: float) -> float:
    """Sigmoid spoilage probability."""
    progress = days_elapsed / max(adjusted_shelf_life, 0.5)
    prob = 1 / (1 + math.exp(-8 * (progress - 0.6)))
    return round(min(max(prob, 0.01), 0.99), 4)


def _risk_level(prob: float) -> int:
    """Classify risk level from probability."""
    if prob < 0.2:
        return 0   # low
    elif prob < 0.5:
        return 1   # medium
    elif prob < 0.8:
        return 2   # high
    else:
        return 3   # critical


def generate_single_sample(rng: np.random.Generator) -> Dict:
    """
    Generate one realistic spoilage data sample.

    Uses domain-aware distributions to create diverse but realistic scenarios.
    """
    # Pick crop
    crop_name = rng.choice(CROP_NAMES)
    profile = CROP_PROFILES[crop_name]

    # Storage type (weighted: most farmers use ambient in India)
    storage_type = int(rng.random() < 0.3)  # 30% cold storage
    base_shelf = profile["cold_days"] if storage_type else profile["ambient_days"]

    # Season (weighted towards summer/monsoon — peak harvest seasons)
    season_weights = [0.35, 0.30, 0.20, 0.15]
    season = rng.choice(list(INDIAN_SEASONS.keys()), p=season_weights)
    season_data = INDIAN_SEASONS[season]

    # Temperature: seasonal ambient OR cold storage range
    if storage_type == 1:
        # Cold storage — near optimal with some variation
        opt_mid = (profile["optimal_temp"][0] + profile["optimal_temp"][1]) / 2
        temperature = rng.normal(opt_mid, 3.0)
        # Sometimes cold chain breaks
        if rng.random() < 0.1:
            temperature = rng.normal(season_data["temp_mean"], 5)  # cold chain failure
    else:
        temperature = rng.normal(season_data["temp_mean"], season_data["temp_std"])

    temperature = round(np.clip(temperature, -5, 50), 1)

    # Humidity
    if storage_type == 1:
        opt_hum_mid = (profile["optimal_humidity"][0] + profile["optimal_humidity"][1]) / 2
        humidity = rng.normal(opt_hum_mid, 5)
    else:
        humidity = rng.normal(season_data["humidity_mean"], season_data["humidity_std"])

    humidity = round(np.clip(humidity, 10, 100), 1)

    # Days since harvest (0 to 2x base shelf life, skewed towards early)
    max_days = base_shelf * 2.0
    days_since_harvest = round(rng.exponential(scale=base_shelf * 0.5))
    days_since_harvest = min(days_since_harvest, int(max_days))

    # Transport hours (most trips < 12h, some long-haul)
    if rng.random() < 0.15:
        transport_hours = round(rng.uniform(12, 48), 1)  # long haul
    else:
        transport_hours = round(rng.exponential(scale=3.0), 1)
    transport_hours = min(transport_hours, 72)

    # Initial quality (most produce starts good)
    initial_quality = round(rng.beta(8, 2) * 100)  # skewed high
    initial_quality = int(np.clip(initial_quality, 10, 100))

    # Quantity
    quantity_kg = round(rng.lognormal(mean=3.0, sigma=1.2))
    quantity_kg = int(np.clip(quantity_kg, 1, 5000))

    # ── Compute targets ──────────────────────────────────────────

    # Temperature deviation from optimal
    opt_min, opt_max = profile["optimal_temp"]
    if temperature < opt_min:
        temp_deviation = opt_min - temperature
    elif temperature > opt_max:
        temp_deviation = temperature - opt_max
    else:
        temp_deviation = 0.0

    # Humidity deviation from optimal
    hum_min, hum_max = profile["optimal_humidity"]
    if humidity < hum_min:
        hum_deviation = hum_min - humidity
    elif humidity > hum_max:
        hum_deviation = humidity - hum_max
    else:
        hum_deviation = 0.0

    # Degradation factors
    temp_f = _temperature_factor(temperature, opt_min, opt_max)
    hum_f = _humidity_factor(humidity, hum_min, hum_max)
    transport_f = 1.0 + (transport_hours * 0.02 * profile["damage_sensitivity"])
    quality_f = 1.0 + (1.0 - initial_quality / 100) * 0.5  # low quality spoils faster
    resp_mult = RESPIRATION_MULTIPLIER[profile["respiration_rate"]]

    total_degradation = temp_f * hum_f * transport_f * quality_f * resp_mult

    # Add realistic noise (±10%)
    noise = rng.normal(1.0, 0.05)
    total_degradation *= max(noise, 0.5)

    # Adjusted shelf life
    adjusted_shelf = max(0.5, base_shelf / total_degradation)

    # Remaining shelf life
    remaining = max(0, adjusted_shelf - days_since_harvest)

    # Spoilage probability
    prob = _spoilage_probability(days_since_harvest, adjusted_shelf)

    # Risk level
    risk = _risk_level(prob)

    return {
        # Features
        "crop_type": crop_name,
        "crop_type_idx": CROP_TO_IDX[crop_name],
        "storage_type": storage_type,
        "temperature_c": temperature,
        "humidity_pct": humidity,
        "days_since_harvest": days_since_harvest,
        "transport_hours": transport_hours,
        "initial_quality_score": initial_quality,
        "quantity_kg": quantity_kg,
        "damage_sensitivity": profile["damage_sensitivity"],
        "base_shelf_life_days": base_shelf,
        "temp_deviation": round(temp_deviation, 2),
        "humidity_deviation": round(hum_deviation, 2),
        "respiration_multiplier": resp_mult,
        # Targets
        "remaining_shelf_life_days": round(remaining, 1),
        "spoilage_probability": prob,
        "risk_level": risk,
        # Metadata (not used as features)
        "season": season,
        "category": profile["category"],
    }


def generate_dataset(
    n_samples: int = 50000,
    seed: int = 42,
    balance_crops: bool = True,
) -> pd.DataFrame:
    """
    Generate a full synthetic spoilage dataset.

    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.
        balance_crops: If True, ensures equal representation of all crops.

    Returns:
        DataFrame with features and targets.
    """
    rng = np.random.default_rng(seed)
    samples = []

    if balance_crops:
        per_crop = n_samples // NUM_CROPS
        remainder = n_samples % NUM_CROPS

        for i, crop_name in enumerate(CROP_NAMES):
            count = per_crop + (1 if i < remainder else 0)
            for _ in range(count):
                sample = generate_single_sample(rng)
                # Override crop for balance
                sample["crop_type"] = crop_name
                sample["crop_type_idx"] = CROP_TO_IDX[crop_name]
                profile = CROP_PROFILES[crop_name]
                sample["damage_sensitivity"] = profile["damage_sensitivity"]
                sample["respiration_multiplier"] = RESPIRATION_MULTIPLIER[profile["respiration_rate"]]
                sample["category"] = profile["category"]
                # Recompute base shelf life for correct crop
                storage_type = sample["storage_type"]
                sample["base_shelf_life_days"] = (
                    profile["cold_days"] if storage_type else profile["ambient_days"]
                )
                samples.append(sample)
    else:
        for _ in range(n_samples):
            samples.append(generate_single_sample(rng))

    df = pd.DataFrame(samples)

    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return df


def split_dataset(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train/val/test with stratification by crop and risk level.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6

    # Create stratification key
    df["_strat_key"] = df["crop_type"] + "_" + df["risk_level"].astype(str)

    # Group by strat key and assign splits
    train_dfs, val_dfs, test_dfs = [], [], []

    for key, group in df.groupby("_strat_key"):
        n = len(group)
        group = group.sample(frac=1, random_state=seed)  # shuffle within group
        n_train = max(1, int(n * train_ratio))
        n_val = max(1, int(n * val_ratio))

        train_dfs.append(group.iloc[:n_train])
        val_dfs.append(group.iloc[n_train:n_train + n_val])
        test_dfs.append(group.iloc[n_train + n_val:])

    train_df = pd.concat(train_dfs).sample(frac=1, random_state=seed).reset_index(drop=True)
    val_df = pd.concat(val_dfs).sample(frac=1, random_state=seed).reset_index(drop=True)
    test_df = pd.concat(test_dfs).sample(frac=1, random_state=seed).reset_index(drop=True)

    # Drop temp column
    for d in [train_df, val_df, test_df]:
        d.drop(columns=["_strat_key"], inplace=True)

    return train_df, val_df, test_df


def save_dataset(
    df: pd.DataFrame,
    output_dir: str = "data",
    prefix: str = "spoilage",
):
    """Save dataset to CSV and metadata to JSON."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save CSV
    csv_path = output_path / f"{prefix}_full.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved full dataset: {csv_path} ({len(df)} samples)")

    # Split and save
    train_df, val_df, test_df = split_dataset(df)
    train_df.to_csv(output_path / f"{prefix}_train.csv", index=False)
    val_df.to_csv(output_path / f"{prefix}_val.csv", index=False)
    test_df.to_csv(output_path / f"{prefix}_test.csv", index=False)
    print(f"  Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

    # Save metadata
    metadata = {
        "num_samples": len(df),
        "num_crops": NUM_CROPS,
        "crop_names": CROP_NAMES,
        "crop_to_idx": CROP_TO_IDX,
        "feature_columns": FEATURE_COLUMNS,
        "target_columns": TARGET_COLUMNS,
        "risk_levels": RISK_LEVELS,
        "splits": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
        },
        "class_distribution": {
            "train": train_df["risk_level"].value_counts().to_dict(),
            "val": val_df["risk_level"].value_counts().to_dict(),
            "test": test_df["risk_level"].value_counts().to_dict(),
        },
    }
    meta_path = output_path / f"{prefix}_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata: {meta_path}")

    return train_df, val_df, test_df


def print_dataset_summary(df: pd.DataFrame):
    """Print a concise summary of the generated dataset."""
    print("\n" + "=" * 60)
    print("SPOILAGE PREDICTION DATASET SUMMARY")
    print("=" * 60)
    print(f"Total samples: {len(df):,}")
    print(f"Crops: {NUM_CROPS}")
    print(f"Features: {len(FEATURE_COLUMNS)}")
    print(f"Targets: {len(TARGET_COLUMNS)}")

    print("\n── Crop distribution ──")
    for crop, count in df["crop_type"].value_counts().sort_index().items():
        print(f"  {crop:15s}: {count:5d} ({count/len(df)*100:.1f}%)")

    print("\n── Risk level distribution ──")
    for risk_idx, count in sorted(df["risk_level"].value_counts().items()):
        label = RISK_LEVELS[risk_idx]
        print(f"  {label:10s} ({risk_idx}): {count:5d} ({count/len(df)*100:.1f}%)")

    print("\n── Feature statistics ──")
    for col in FEATURE_COLUMNS:
        if col in df.columns:
            print(f"  {col:28s}: mean={df[col].mean():8.2f}  std={df[col].std():8.2f}  "
                  f"min={df[col].min():8.2f}  max={df[col].max():8.2f}")

    print("\n── Target statistics ──")
    for col in TARGET_COLUMNS:
        if col in df.columns:
            print(f"  {col:28s}: mean={df[col].mean():8.2f}  std={df[col].std():8.2f}  "
                  f"min={df[col].min():8.2f}  max={df[col].max():8.2f}")

    print("=" * 60)


# ── CLI entry point ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic spoilage dataset")
    parser.add_argument("--samples", type=int, default=50000, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    parser.add_argument("--no-balance", action="store_true", help="Don't balance crops")

    args = parser.parse_args()

    print(f"Generating {args.samples:,} synthetic spoilage samples...")
    df = generate_dataset(
        n_samples=args.samples,
        seed=args.seed,
        balance_crops=not args.no_balance,
    )
    print_dataset_summary(df)
    save_dataset(df, output_dir=args.output)
    print("\nDone!")
