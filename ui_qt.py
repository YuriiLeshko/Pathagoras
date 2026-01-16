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
import re

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
        fm = painter.fontMetrics()

        def clamp(val: int, lo: int, hi: int) -> int:
            return max(lo, min(val, hi))

        def fmt(name: str, value) -> str:
            """Build label like 'b = 12.34' or just 'b' if value missing."""
            if not self.has_result or value is None:
                return name
            # Use a compact format; still may be long -> will be elided later
            return f"{name} = {value:g}"

        def draw_centered_elided_text(x_center: int, y: int, text: str, max_width: int):
            """
            Draw elided text (with ellipsis if needed) centered around x_center.
            """
            elided = fm.elidedText(text, Qt.ElideRight, max_width)
            text_w = fm.horizontalAdvance(elided)
            painter.drawText(x_center - text_w // 2, y, elided)

        def draw_elided_text(x: int, y: int, text: str, max_width: int):
            """Draw text clipped to max_width using ellipsis if needed."""
            elided = fm.elidedText(text, Qt.ElideRight, max_width)
            painter.drawText(x, y, elided)

        # Midpoints for labels
        mid_ca = ((point_c[0] + point_a[0]) // 2, (point_c[1] + point_a[1]) // 2)  # bottom leg
        mid_cb = ((point_c[0] + point_b[0]) // 2, (point_c[1] + point_b[1]) // 2)  # left leg
        mid_ba = ((point_b[0] + point_a[0]) // 2, (point_b[1] + point_a[1]) // 2)  # hypotenuse

        # b: center the TEXT around the midpoint of the bottom leg
        b_text = fmt("b", self.result_b)
        b_y = clamp(mid_ca[1] - 10, margin, h - 5)  # keep inside widget

        b_max_left = mid_ca[0] - 5
        b_max_right = w - 5 - mid_ca[0]
        b_max_w = max(60, 2 * min(b_max_left, b_max_right))

        draw_centered_elided_text(mid_ca[0], b_y, b_text, max_width=b_max_w)

        # c: use the previous "anchored near the midpoint" approach to avoid overlapping the slanted side
        c_text = fmt("c", self.result_c)
        c_x = clamp(mid_ba[0] + 10, 5, w - margin)
        c_y = clamp(mid_ba[1] - 10, margin, h - 5)
        draw_elided_text(c_x, c_y, c_text, max_width=w - c_x - 5)

        # a: vertical text along the left leg (better for long values), centered
        a_text = fmt("a", self.result_a)

        painter.save()
        a_x = clamp(mid_cb[0] - 25, 5, w - 5)
        a_y = clamp(mid_cb[1] + 10, margin, h - margin)

        painter.translate(a_x, a_y)
        painter.rotate(-90)

        max_w_rot = max(60, h - 2 * margin)
        elided_a = fm.elidedText(a_text, Qt.ElideRight, max_w_rot)
        a_text_w = fm.horizontalAdvance(elided_a)

        # Center the vertical text around the rotation origin
        painter.drawText(-a_text_w // 2, 0, elided_a)
        painter.restore()



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
        self.status_label.setFont(QFont("Arial", 16))
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Action button
        self.action_button = QPushButton("—")
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self.on_action_clicked)
        input_row.addWidget(self.action_button)

        layout.addLayout(input_row)

        # When True, input changes must NOT overwrite the last result message.
        self._showing_result = False


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
        if getattr(self, "_showing_result", False):
            any_text = any((
                self.a_edit.text().strip(),
                self.b_edit.text().strip(),
                self.c_edit.text().strip(),
            ))
            if not any_text:
                return
            self._showing_result = False

        filled = self._filled_count()

        if filled == 2:
            self.action_button.setEnabled(True)
            self.action_button.setText("Calculate")
            self.status_label.setText(self._sentence_wrap(
                "Leave the field empty for the value you want to compute (a, b, or c)."
            ))
            return

        if filled == 3:
            self.action_button.setEnabled(True)
            self.action_button.setText("Verify")
            self.status_label.setText(self._sentence_wrap(
                "Click 'Verify' to check whether the triangle is right-angled. "
                "Input will be sorted: largest will be treated as hypotenuse."
            ))
            return

        self.action_button.setEnabled(False)
        self.action_button.setText("—")
        self.status_label.setText(self._sentence_wrap("Enter two values to compute or three to verify"))

    def _format_abc(self, a: float, b: float, c: float) -> str:
        """Human-readable values line."""
        return f"a = {a:g}, b = {b:g}, c = {c:g}"

    def _sentence_wrap(self, text: str) -> str:
        """
        Make the status output more readable by putting each sentence on a new line.

        We split only when a sentence-ending punctuation is followed by whitespace:
            '.', '!' or '?' + whitespace -> newline

        This avoids breaking:
        - decimal numbers: 3.14 (no whitespace after '.')
        - scientific notation: 1e-3
        - version-like tokens: v1.2.3 (no whitespace)
        """
        text = (text or "").strip()
        if not text:
            return ""

        # Replace ". " / "! " / "? " (and multiple spaces) with ".\n" etc.
        return re.sub(r'([.!?])\s+', r'\1\n', text)

    def _clear_inputs(self) -> None:
        """Clear input fields after an action click, without overwriting the result message."""
        self.a_edit.blockSignals(True)
        self.b_edit.blockSignals(True)
        self.c_edit.blockSignals(True)

        self.a_edit.clear()
        self.b_edit.clear()
        self.c_edit.clear()

        self.a_edit.blockSignals(False)
        self.b_edit.blockSignals(False)
        self.c_edit.blockSignals(False)

        # Reset the button state, but DO NOT touch status_label here.
        self.action_button.setEnabled(False)
        self.action_button.setText("—")

    def on_action_clicked(self):
        """
        Read inputs -> call core -> show results.

        - Status shows ONLY core message, formatted into sentences-per-line.
        - Canvas displays exactly the values returned by core.
        - Inputs are cleared after the action.
        """
        a_txt = self._normalized_text(self.a_edit.text())
        b_txt = self._normalized_text(self.b_edit.text())
        c_txt = self._normalized_text(self.c_edit.text())

        result = core.proceed_data({"a": a_txt, "b": b_txt, "c": c_txt})

        # Lock status to keep result visible
        self._showing_result = True

        self.status_label.setText(self._sentence_wrap(result.message))

        if result.is_valid and result.a is not None and result.b is not None and result.c is not None:
            self.canvas.show_result(result.a, result.b, result.c)
        else:
            self.canvas.show_placeholder()

        self._clear_inputs()


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
