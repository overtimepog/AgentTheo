"""
Stealth module for browser automation
Implements advanced anti-detection techniques for Playwright
"""

from .stealth_config import StealthConfig, apply_stealth
from .evasions import EVASIONS

__all__ = ['StealthConfig', 'apply_stealth', 'EVASIONS']