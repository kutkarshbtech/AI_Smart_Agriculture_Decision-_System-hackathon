"""
Training script for fruit freshness classification model.

Two-phase transfer learning:
    Phase 1: Train classifier head only (backbone frozen)
    Phase 2: Fine-tune backbone + head (gradual unfreezing)

Usage:
    python train.py --data_dir data/ --epochs 25 --batch_size 32
    python train.py --data_dir data/ --epochs 25 --phase both --lr 0.001
"""

import os
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, ReduceLROnPlateau
from torch.utils.data import DataLoader

from dataset import (
    create_data_loaders,
    save_class_mapping,
    NUM_CLASSES,
    IDX_TO_CLASS,
    CLASS_NAMES,
)
from model import build_model, FreshnessClassifier


# ── Training Engine ───────────────────────────────────────────────

class Trainer:
    """
    Training engine with:
    - Mixed precision training (AMP)
    - Gradient accumulation
    - Learning rate scheduling
    - Early stopping
    - Model checkpointing
    - Training history logging
    """

    def __init__(
        self,
        model: FreshnessClassifier,
        device: torch.device,
        output_dir: str = "models/",
        experiment_name: str = "freshness_v1",
    ):
        self.model = model.to(device)
        self.device = device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.experiment_name = experiment_name

        # Loss function with label smoothing for better generalization
        self.criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

        # Mixed precision scaler
        self.scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None

        # Training history
        self.history: Dict[str, List[float]] = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
            "lr": [],
        }

        self.best_val_acc = 0.0
        self.best_epoch = 0

    def train_one_epoch(
        self,
        train_loader: DataLoader,
        optimizer: optim.Optimizer,
        epoch: int,
        total_epochs: int,
        grad_accum_steps: int = 1,
    ) -> Tuple[float, float]:
        """Train for one epoch."""
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        optimizer.zero_grad()

        for batch_idx, (images, labels) in enumerate(train_loader):
            images = images.to(self.device)
            labels = labels.to(self.device)

            # Mixed precision forward pass
            if self.scaler:
                with torch.amp.autocast("cuda"):
                    outputs = self.model(images)
                    loss = self.criterion(outputs, labels)
                    loss = loss / grad_accum_steps

                self.scaler.scale(loss).backward()

                if (batch_idx + 1) % grad_accum_steps == 0:
                    self.scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                    self.scaler.step(optimizer)
                    self.scaler.update()
                    optimizer.zero_grad()
            else:
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                loss = loss / grad_accum_steps
                loss.backward()

                if (batch_idx + 1) % grad_accum_steps == 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                    optimizer.step()
                    optimizer.zero_grad()

            running_loss += loss.item() * grad_accum_steps * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            # Progress
            if (batch_idx + 1) % 20 == 0 or batch_idx == len(train_loader) - 1:
                batch_acc = 100.0 * correct / total
                print(
                    f"  Epoch [{epoch+1}/{total_epochs}] "
                    f"Batch [{batch_idx+1}/{len(train_loader)}] "
                    f"Loss: {loss.item():.4f} Acc: {batch_acc:.1f}%"
                )

        epoch_loss = running_loss / total
        epoch_acc = 100.0 * correct / total
        return epoch_loss, epoch_acc

    @torch.no_grad()
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """Evaluate on validation set."""
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in val_loader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            outputs = self.model(images)
            loss = self.criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        val_loss = running_loss / total
        val_acc = 100.0 * correct / total
        return val_loss, val_acc

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 25,
        lr: float = 0.001,
        weight_decay: float = 1e-4,
        patience: int = 7,
        scheduler_type: str = "cosine",
        grad_accum_steps: int = 1,
    ) -> Dict[str, List[float]]:
        """
        Full training loop.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            epochs: Number of training epochs
            lr: Learning rate
            weight_decay: L2 regularization
            patience: Early stopping patience
            scheduler_type: "cosine" or "plateau"
            grad_accum_steps: Gradient accumulation steps

        Returns:
            Training history dict
        """
        # Optimizer — only update trainable params
        trainable_params = filter(lambda p: p.requires_grad, self.model.parameters())
        optimizer = optim.AdamW(trainable_params, lr=lr, weight_decay=weight_decay)

        # Learning rate scheduler
        if scheduler_type == "cosine":
            scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=5, T_mult=2, eta_min=1e-6)
        else:
            scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=3)

        early_stop_counter = 0

        print(f"\n{'='*60}")
        print(f"Starting training: {self.experiment_name}")
        print(f"  Device: {self.device}")
        print(f"  Epochs: {epochs}")
        print(f"  LR: {lr}")
        print(f"  Trainable params: {self.model.get_trainable_params():,}")
        print(f"{'='*60}\n")

        start_time = time.time()

        for epoch in range(epochs):
            epoch_start = time.time()

            # Train
            train_loss, train_acc = self.train_one_epoch(
                train_loader, optimizer, epoch, epochs, grad_accum_steps
            )

            # Validate
            val_loss, val_acc = self.validate(val_loader)

            # Get current LR
            current_lr = optimizer.param_groups[0]["lr"]

            # Update scheduler
            if scheduler_type == "cosine":
                scheduler.step()
            else:
                scheduler.step(val_acc)

            # Record history
            self.history["train_loss"].append(train_loss)
            self.history["train_acc"].append(train_acc)
            self.history["val_loss"].append(val_loss)
            self.history["val_acc"].append(val_acc)
            self.history["lr"].append(current_lr)

            epoch_time = time.time() - epoch_start

            print(
                f"\nEpoch {epoch+1}/{epochs} ({epoch_time:.1f}s) | "
                f"Train Loss: {train_loss:.4f} Acc: {train_acc:.1f}% | "
                f"Val Loss: {val_loss:.4f} Acc: {val_acc:.1f}% | "
                f"LR: {current_lr:.6f}"
            )

            # Save best model
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                self.best_epoch = epoch + 1
                early_stop_counter = 0

                self._save_checkpoint(epoch, val_acc, optimizer, is_best=True)
                print(f"  ✓ New best model saved! Val Acc: {val_acc:.2f}%")
            else:
                early_stop_counter += 1
                print(f"  No improvement for {early_stop_counter}/{patience} epochs")

            # Early stopping
            if early_stop_counter >= patience:
                print(f"\nEarly stopping triggered after {epoch+1} epochs.")
                break

        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"Training complete in {total_time/60:.1f} minutes")
        print(f"Best val accuracy: {self.best_val_acc:.2f}% (epoch {self.best_epoch})")
        print(f"{'='*60}")

        # Save training history
        self._save_history()

        return self.history

    def _save_checkpoint(
        self, epoch: int, val_acc: float, optimizer, is_best: bool = False
    ):
        """Save model checkpoint."""
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "val_acc": val_acc,
            "num_classes": self.model.num_classes,
            "class_names": CLASS_NAMES,
        }

        if is_best:
            path = self.output_dir / f"{self.experiment_name}_best.pth"
        else:
            path = self.output_dir / f"{self.experiment_name}_epoch{epoch+1}.pth"

        torch.save(checkpoint, path)

    def _save_history(self):
        """Save training history to JSON."""
        history_path = self.output_dir / f"{self.experiment_name}_history.json"
        with open(history_path, "w") as f:
            json.dump(self.history, f, indent=2)
        print(f"Training history saved to: {history_path}")


# ── Two-Phase Training ────────────────────────────────────────────

def train_two_phase(
    data_dir: str,
    output_dir: str = "models/",
    phase1_epochs: int = 10,
    phase2_epochs: int = 15,
    batch_size: int = 32,
    phase1_lr: float = 0.001,
    phase2_lr: float = 0.0001,
    num_workers: int = 4,
    experiment_name: str = "freshness_v1",
):
    """
    Two-phase transfer learning training pipeline.

    Phase 1: Feature extraction — train classifier head only
    Phase 2: Fine-tuning — unfreeze last 5 backbone blocks + classifier
    """
    # Device selection
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Data loaders
    train_loader, val_loader, test_loader = create_data_loaders(
        data_dir, batch_size=batch_size, num_workers=num_workers
    )

    # Build model
    model = build_model(num_classes=NUM_CLASSES, pretrained=True, freeze_backbone=True)

    # Save class mapping
    os.makedirs(output_dir, exist_ok=True)
    save_class_mapping(os.path.join(output_dir, "class_mapping.json"))

    trainer = Trainer(model, device, output_dir, experiment_name)

    # ── Phase 1: Train classifier head ──
    print("\n" + "="*60)
    print("PHASE 1: Feature Extraction (backbone frozen)")
    print("="*60)

    trainer.train(
        train_loader,
        val_loader,
        epochs=phase1_epochs,
        lr=phase1_lr,
        scheduler_type="cosine",
    )

    # ── Phase 2: Fine-tune backbone ──
    print("\n" + "="*60)
    print("PHASE 2: Fine-Tuning (unfreezing backbone layers 14+)")
    print("="*60)

    model.unfreeze_backbone(from_layer=14)
    model.summary()

    # Lower LR for fine-tuning to avoid destroying pretrained features
    trainer.train(
        train_loader,
        val_loader,
        epochs=phase2_epochs,
        lr=phase2_lr,
        scheduler_type="plateau",
        patience=5,
    )

    # ── Evaluate on test set ──
    if test_loader:
        print("\n" + "="*60)
        print("FINAL EVALUATION ON TEST SET")
        print("="*60)
        test_loss, test_acc = trainer.validate(test_loader)
        print(f"Test Loss: {test_loss:.4f} | Test Accuracy: {test_acc:.2f}%")

    return model, trainer.history


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Train fruit freshness detection model"
    )
    parser.add_argument("--data_dir", type=str, default="data/",
                        help="Path to dataset directory")
    parser.add_argument("--output_dir", type=str, default="models/",
                        help="Path to save trained models")
    parser.add_argument("--epochs", type=int, default=25,
                        help="Total epochs (split across phases)")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Training batch size")
    parser.add_argument("--lr", type=float, default=0.001,
                        help="Initial learning rate")
    parser.add_argument("--phase", choices=["head", "finetune", "both"], default="both",
                        help="Training phase to run")
    parser.add_argument("--num_workers", type=int, default=4,
                        help="Data loader workers")
    parser.add_argument("--name", type=str, default="freshness_v1",
                        help="Experiment name for checkpoints")

    args = parser.parse_args()

    if args.phase == "both":
        phase1_epochs = args.epochs // 3
        phase2_epochs = args.epochs - phase1_epochs

        train_two_phase(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            phase1_epochs=phase1_epochs,
            phase2_epochs=phase2_epochs,
            batch_size=args.batch_size,
            phase1_lr=args.lr,
            phase2_lr=args.lr * 0.1,
            num_workers=args.num_workers,
            experiment_name=args.name,
        )
    elif args.phase == "head":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        train_loader, val_loader, _ = create_data_loaders(
            args.data_dir, args.batch_size, args.num_workers
        )
        model = build_model(freeze_backbone=True)
        trainer = Trainer(model, device, args.output_dir, args.name)
        trainer.train(train_loader, val_loader, epochs=args.epochs, lr=args.lr)
    else:
        # Fine-tune: load best model from phase 1
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        train_loader, val_loader, _ = create_data_loaders(
            args.data_dir, args.batch_size, args.num_workers
        )
        model = build_model(freeze_backbone=False)

        checkpoint_path = os.path.join(args.output_dir, f"{args.name}_best.pth")
        if os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=device)
            model.load_state_dict(checkpoint["model_state_dict"])
            print(f"Loaded checkpoint from: {checkpoint_path}")

        model.unfreeze_backbone(from_layer=14)
        trainer = Trainer(model, device, args.output_dir, args.name)
        trainer.train(
            train_loader, val_loader,
            epochs=args.epochs, lr=args.lr * 0.1,
            scheduler_type="plateau", patience=5
        )


if __name__ == "__main__":
    main()
