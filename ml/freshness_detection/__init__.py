"""
Freshness Detection Module

MobileNetV2-based computer vision model for detecting fruit/vegetable freshness.
"""

from .model import FreshnessClassifier
from .dataset import NUM_CLASSES, CLASS_NAMES

__all__ = ['FreshnessClassifier', 'NUM_CLASSES', 'CLASS_NAMES']
