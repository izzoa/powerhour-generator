"""
PowerHour Generator Package

A comprehensive tool for creating custom PowerHour videos with both GUI and CLI interfaces.
"""

__version__ = "1.1.0"  # canonical source — setup.py, scripts/build.py, powerhour.spec, and Makefile parse this
__author__ = "Anthony Izzo"

from .powerhour_gui import PowerHourGUI
from .powerhour_processor import ProcessorThread

__all__ = ['PowerHourGUI', 'ProcessorThread']