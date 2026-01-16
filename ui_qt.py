"""
ui_qt.py — Graphical UI for the Pythagoras Tool (PySide6).

Integration with business logic
-------------------------------
This UI connects to `core.proceed_data(...)`, which returns a `TriangleData` object
and never propagates ValueError to the UI layer.

Button behavior (critical requirement)
--------------------------------------
The action button behaves strictly as follows:
- Exactly 2 non-empty fields (a/b/c)  -> button enabled, text = "Calculate"
- Exactly 3 non-empty fields (a/b/c)  -> button enabled, text = "Verify"
- Any other case (0, 1 fields)        -> button disabled, text = "—"

On click:
- reads texts from a/b/c fields,
- normalizes decimal comma to dot for user convenience (e.g., "3,5" -> "3.5"),
- calls `core.proceed_data({"a": a_txt, "b": b_txt, "c": c_txt})`,
- shows `result.message`,
- if result is valid and all sides exist -> draws numeric values on the canvas,
  otherwise shows placeholder.

Notes on style
--------------
- Existing code comments are preserved.
- Variable names avoid leading capital letters (PEP8 / IDE warnings).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QFont
import sys

import core


class TriangleCanvas(QFrame):
    """
    Drawing area that shows a placeholder right isosceles triangle
    with labels a, b, c. Later you can extend it to draw numeric values.
    """
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(260)
        self.setFrameShape(QFrame.StyledPanel)

        # If later you want to draw a computed triangle, store values here.
        self.has_result = False
        self.result_a = None
        self.result_b = None
        self.result_c = None

    def show_placeholder(self):
        """Switch to placeholder mode (no numeric values are displayed)."""
        self.has_result = False
        self.update()

    def show_result(self, a: float, b: float, c: float):
        """Switch to result mode and display numeric values for a, b, c."""
        self.has_result = True
        self.result_a, self.result_b, self.result_c = a, b, c
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        palette = self.palette()
        text_color = palette.color(self.foregroundRole())

        pen = QPen(text_color, 2)
        painter.setPen(pen)

        w, h = self.width(), self.height()
        margin = 40

        # Right angle at bottom-left (C), isosceles legs
        point_c = (margin, h - margin)           # bottom-left
        point_a = (w - margin, h - margin)       # bottom-right
        point_b = (margin, margin)               # top-left

        # Draw triangle edges
        painter.drawLine(point_c[0], point_c[1], point_a[0], point_a[1])  # base (leg b)
        painter.drawLine(point_c[0], point_c[1], point_b[0], point_b[1])  # vertical (leg a)
        painter.drawLine(point_b[0], point_b[1], point_a[0], point_a[1])  # hypotenuse (c)

        # Draw right-angle marker at C
        ra = 18
        painter.drawLine(point_c[0], point_c[1], point_c[0] + ra, point_c[1])
        painter.drawLine(point_c[0], point_c[1], point_c[0], point_c[1] - ra)
        painter.drawLine(point_c[0] + ra, point_c[1], point_c[0] + ra, point_c[1] - ra)
        painter.drawLine(point_c[0], point_c[1] - ra, point_c[0] + ra, point_c[1] - ra)

        # Labels font
        painter.setFont(QFont("Arial", 12))
        painter.setPen(text_color)

        # Midpoints for labels
        mid_ca = ((point_c[0] + point_a[0]) // 2, (point_c[1] + point_a[1]) // 2)  # bottom leg
        mid_cb = ((point_c[0] + point_b[0]) // 2, (point_c[1] + point_b[1]) // 2)  # left leg
        mid_ba = ((point_b[0] + point_a[0]) // 2, (point_b[1] + point_a[1]) // 2)  # hypotenuse

        # Offsets for nicer placement
        painter.drawText(mid_cb[0] - 25, mid_cb[1], "a")          # left leg
        painter.drawText(mid_ca[0], mid_ca[1] + 25, "b")          # bottom leg
        painter.drawText(mid_ba[0] + 10, mid_ba[1] - 10, "c")     # hypotenuse

        # Optional: show numeric values only after computation/verification
        if self.has_result:
            painter.setFont(QFont("Arial", 14))
            painter.setPen(text_color)

            # Place numbers near labels
            painter.drawText(mid_cb[0] - 25, mid_cb[1] + 30, f"{self.result_a:g}")
            painter.drawText(mid_ca[0] - 15, mid_ca[1] + 75, f"{self.result_b:g}")
            painter.drawText(mid_ba[0] + 10, mid_ba[1] + 25, f"{self.result_c:g}")


class MainWindow(QWidget):
    """
    Main application window.

    Responsibilities
    ----------------
    - Collect user input from three text fields (a, b, c).
    - Maintain the correct state and label of the action button:
        * 2 fields filled -> "Calculate"
        * 3 fields filled -> "Verify"
        * otherwise       -> disabled, "—"
    - Call the core orchestration function `core.proceed_data`.
    - Display the returned status message and (when possible) numeric results on the canvas.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pythagoras Tool")
        self.resize(720, 520)

        layout = QVBoxLayout(self)

        # --- Drawing area (placeholder visible from the start) ---
        self.canvas = TriangleCanvas()
        self.canvas.show_placeholder()
        layout.addWidget(self.canvas)

        # --- Input row with labels before fields ---
        input_row = QHBoxLayout()

        # a (leg)
        input_row.addWidget(QLabel("a:"))
        self.a_edit = QLineEdit()
        self.a_edit.setPlaceholderText("leg")
        self.a_edit.textChanged.connect(self.on_input_changed)
        input_row.addWidget(self.a_edit)

        # b (leg)
        input_row.addWidget(QLabel("b:"))
        self.b_edit = QLineEdit()
        self.b_edit.setPlaceholderText("leg")
        self.b_edit.textChanged.connect(self.on_input_changed)
        input_row.addWidget(self.b_edit)

        # c (hypotenuse)
        input_row.addWidget(QLabel("c:"))
        self.c_edit = QLineEdit()
        self.c_edit.setPlaceholderText("hypotenuse")
        self.c_edit.textChanged.connect(self.on_input_changed)
        input_row.addWidget(self.c_edit)

        # --- Status message ---
        self.status_label = QLabel("Enter two values to compute or three to verify")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Action button
        self.action_button = QPushButton("—")
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self.on_action_clicked)
        input_row.addWidget(self.action_button)

        layout.addLayout(input_row)

    def _normalized_text(self, txt: str) -> str:
        """
        Normalize user input before passing it to core:
        - strips spaces
        - converts decimal comma to dot (e.g., '3,5' -> '3.5')
        """
        return txt.strip().replace(",", ".")

    def _filled_count(self) -> int:
        """Return how many of the three fields contain non-empty text."""
        values = (
            self.a_edit.text().strip(),
            self.b_edit.text().strip(),
            self.c_edit.text().strip(),
        )
        return sum(bool(v) for v in values)

    def on_input_changed(self):
        """
        Update button state and guidance message whenever input changes.

        Button text rules:
        - filled == 2 -> enabled, 'Calculate'
        - filled == 3 -> enabled, 'Verify'
        - else        -> disabled, '—'
        """
        filled = self._filled_count()

        if filled == 2:
            self.action_button.setEnabled(True)
            self.action_button.setText("Calculate")
            self.status_label.setText("Leave the field empty for the value you want to compute (a, b, or c).")
            return

        if filled == 3:
            self.action_button.setEnabled(True)
            self.action_button.setText("Verify")
            self.status_label.setText(
                "Click 'Verify' to check whether the triangle is right-angled."
                "Input will be sorted: largest will be treated as hypotenuse."
            )
            return

        self.action_button.setEnabled(False)
        self.action_button.setText("—")
        self.status_label.setText("Enter two values to compute or three to verify")

    def _format_abc(self, a: float, b: float, c: float) -> str:
        """Human-readable values for status line."""
        return f"a={a:g}, b={b:g}, c={c:g}"

    def _status_with_values(self, result) -> str:
        """
        Build a readable status message:
        - keep core message
        - append computed/verified values when available
        """
        if result.a is None or result.b is None or result.c is None:
            return result.message

        values = self._format_abc(result.a, result.b, result.c)
        # Detect which field user left empty to infer what was computed (UI-side explanation)
        a_filled = bool(self.a_edit.text().strip())
        b_filled = bool(self.b_edit.text().strip())
        c_filled = bool(self.c_edit.text().strip())

        if sum([a_filled, b_filled, c_filled]) == 2:
            if not c_filled:
                return f"{result.message}. Hypotenuse: c={result.c:g}. ({values})"
            if not a_filled:
                return f"{result.message}. Leg: a={result.a:g}. ({values})"
            if not b_filled:
                return f"{result.message}. Leg: b={result.b:g}. ({values})"

        # Verify mode (3 filled)
        return f"{result.message}. ({values})"

    def on_action_clicked(self):
        """
        Read inputs -> call core -> show results.

        Important:
        - We pass raw strings to `core.proceed_data`, because the core layer is responsible
          for parsing/validation and returns a UI-friendly message on any error.
        - We only draw numeric values on the canvas when the result is valid and complete.
        """
        a_txt = self._normalized_text(self.a_edit.text())
        b_txt = self._normalized_text(self.b_edit.text())
        c_txt = self._normalized_text(self.c_edit.text())

        result = core.proceed_data({"a": a_txt, "b": b_txt, "c": c_txt})

        # Status: message + readable values (when available)
        self.status_label.setText(self._status_with_values(result))

        # Canvas must display exactly what core returned
        if result.is_valid and result.a is not None and result.b is not None and result.c is not None:
            self.canvas.show_result(result.a, result.b, result.c)
        else:
            self.canvas.show_placeholder()


def create_window():
    """
    Create and run the Qt application.

    This function is intentionally small and side-effectful:
    it starts the Qt event loop and exits the process when the window closes.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    create_window()
