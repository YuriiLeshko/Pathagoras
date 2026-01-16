
"""
main.py — Application entry point.

This module is responsible only for starting the Qt GUI.
All UI logic lives in ui_qt.py.
"""

from ui_qt import create_window


def main() -> None:
    """Start the Pythagoras Tool GUI application."""
    create_window()


if __name__ == "__main__":
    main()
