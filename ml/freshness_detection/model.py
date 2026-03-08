"""
Freshness Detection Model — MobileNetV2 Transfer Learning

Architecture:
    - Backbone: MobileNetV2 (pretrained on ImageNet)
    - Classifier head: Custom FC layers for fruit freshness classes
    - Progressive unfreezing: Train head first, then fine-tune backbone

Why MobileNetV2:
    - Lightweight (~3.4M params) — suitable for mobile/edge deployment
    - Inverted residual blocks with linear bottlenecks
    - Strong accuracy/efficiency tradeoff for classification
    - Easily exportable to TFLite/ONNX for Android
"""

import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import MobileNet_V2_Weights
from typing import Optional, Tuple

from dataset import NUM_CLASSES


class FreshnessClassifier(nn.Module):
    """
    MobileNetV2-based classifier for fruit freshness detection.

    The model has two training phases:
    1. Feature extraction: Freeze backbone, train only classifier head
    2. Fine-tuning: Unfreeze later backbone layers, train end-to-end with lower LR
    """

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        pretrained: bool = True,
        dropout_rate: float = 0.3,
    ):
        super().__init__()

        # Load pretrained MobileNetV2 backbone
        if pretrained:
            self.backbone = models.mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
        else:
            self.backbone = models.mobilenet_v2(weights=None)

        # Get the feature dimension from MobileNetV2's last conv layer
        # MobileNetV2 outputs 1280-dim features
        in_features = self.backbone.classifier[1].in_features  # 1280

        # Replace the classifier head
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.5),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.3),
            nn.Linear(128, num_classes),
        )

        self.num_classes = num_classes

        # Initialize classifier weights
        self._init_classifier()

    def _init_classifier(self):
        """Kaiming initialization for the custom classifier head."""
        for m in self.backbone.classifier.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass — returns logits (not probabilities)."""
        return self.backbone(x)

    def predict(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict with probabilities.

        Returns:
            (predicted_class_indices, class_probabilities)
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(probs, dim=1)
        return preds, probs

    # ── Freezing/unfreezing for transfer learning ───────────────

    def freeze_backbone(self):
        """Freeze all backbone (feature extractor) layers. Only classifier trains."""
        for param in self.backbone.features.parameters():
            param.requires_grad = False
        print("Backbone frozen — only classifier head will be trained.")

    def unfreeze_backbone(self, from_layer: int = 14):
        """
        Unfreeze backbone layers starting from `from_layer`.

        MobileNetV2 has 19 inverted residual blocks (indices 0–18).
        Typical fine-tuning: unfreeze from layer 14 onward (last ~5 blocks).

        Args:
            from_layer: First layer index to unfreeze (0 = all, 14 = last 5 blocks)
        """
        total_layers = len(self.backbone.features)
        unfrozen = 0

        for i, layer in enumerate(self.backbone.features):
            if i >= from_layer:
                for param in layer.parameters():
                    param.requires_grad = True
                unfrozen += 1
            else:
                for param in layer.parameters():
                    param.requires_grad = False

        print(f"Unfroze {unfrozen}/{total_layers} backbone layers (from layer {from_layer}).")

    def unfreeze_all(self):
        """Unfreeze entire model for full fine-tuning."""
        for param in self.parameters():
            param.requires_grad = True
        print("All layers unfrozen — full fine-tuning mode.")

    def get_trainable_params(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_total_params(self) -> int:
        """Count total parameters."""
        return sum(p.numel() for p in self.parameters())

    def summary(self):
        """Print model summary."""
        total = self.get_total_params()
        trainable = self.get_trainable_params()
        frozen = total - trainable

        print(f"\n{'='*50}")
        print(f"FreshnessClassifier (MobileNetV2)")
        print(f"{'='*50}")
        print(f"  Num classes:       {self.num_classes}")
        print(f"  Total params:      {total:,}")
        print(f"  Trainable params:  {trainable:,}")
        print(f"  Frozen params:     {frozen:,}")
        print(f"  Model size (est):  {total * 4 / 1024 / 1024:.1f} MB (FP32)")
        print(f"{'='*50}\n")


class FreshnessEnsemble(nn.Module):
    """
    Optional: Ensemble of MobileNetV2 variants for higher accuracy.
    Combines predictions from two model variants with learned weights.
    Use this only if you have enough compute and want competition-grade accuracy.
    """

    def __init__(self, num_classes: int = NUM_CLASSES):
        super().__init__()

        self.model1 = FreshnessClassifier(num_classes, pretrained=True, dropout_rate=0.3)
        self.model2 = FreshnessClassifier(num_classes, pretrained=True, dropout_rate=0.4)

        # Learnable ensemble weights
        self.ensemble_weight = nn.Parameter(torch.tensor([0.5, 0.5]))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits1 = self.model1(x)
        logits2 = self.model2(x)

        weights = torch.softmax(self.ensemble_weight, dim=0)
        return weights[0] * logits1 + weights[1] * logits2


def build_model(
    num_classes: int = NUM_CLASSES,
    pretrained: bool = True,
    freeze_backbone: bool = True,
) -> FreshnessClassifier:
    """
    Factory function to build and configure the freshness classifier.

    Args:
        num_classes: Number of output classes
        pretrained: Use ImageNet pretrained weights
        freeze_backbone: Start with frozen backbone (recommended for transfer learning)

    Returns:
        Configured FreshnessClassifier model
    """
    model = FreshnessClassifier(
        num_classes=num_classes,
        pretrained=pretrained,
    )

    if freeze_backbone:
        model.freeze_backbone()

    model.summary()
    return model


if __name__ == "__main__":
    # Quick test
    model = build_model(freeze_backbone=True)

    # Test forward pass
    dummy_input = torch.randn(4, 3, 224, 224)
    output = model(dummy_input)
    print(f"Output shape: {output.shape}")  # Should be [4, NUM_CLASSES]

    preds, probs = model.predict(dummy_input)
    print(f"Predictions: {preds}")
    print(f"Probabilities shape: {probs.shape}")

    # Test unfreeze
    model.unfreeze_backbone(from_layer=14)
    model.summary()
