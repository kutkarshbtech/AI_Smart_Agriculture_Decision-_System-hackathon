"""
Train the price prediction XGBoost model on synthetic data.

Usage:
    python -m ml.pricing.train            # Train with defaults
    python -m ml.pricing.train --samples 50000   # Train with more data
"""
import argparse
from .model import price_model


def main():
    parser = argparse.ArgumentParser(description="Train the price prediction model")
    parser.add_argument(
        "--samples", type=int, default=10_000,
        help="Number of synthetic training samples (default: 10000)"
    )
    args = parser.parse_args()

    print(f"Training price prediction model with {args.samples} samples...")
    price_model.train(n_samples=args.samples)
    print("Done! Model saved.")

    # Quick evaluation
    importance = price_model.get_feature_importance()
    if importance:
        print("\nTop-10 feature importances (gain):")
        for i, (feat, score) in enumerate(list(importance.items())[:10]):
            print(f"  {i + 1}. {feat}: {score:.4f}")


if __name__ == "__main__":
    main()
