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

Computed output field
---------------------
- Shown only after a successful CALCULATE (exactly 2 filled fields).
- Shows only the computed (missing) side: a or b or c.
- Hidden for VERIFY mode and for any invalid result.

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

        self.has_result = False
        self.result_a = None
        self.result_b = None
        self.result_c = None
        self.is_right = False

        self.grid_enabled = True
        self.grid_step_px = 20  # distance between minor grid lines in pixels
        self.grid_major_every = 5  # every N minor lines draw a thicker major line

    def show_placeholder(self):
        """Switch to placeholder mode (no numeric values are displayed)."""
        self.has_result = False
        self.is_right = False
        self.update()

    def show_result(self, a: float, b: float, c: float, is_right: bool):
        """Switch to result mode and display numeric values for a, b, c."""
        self.has_result = True
        self.result_a, self.result_b, self.result_c = a, b, c
        self.is_right = is_right
        self.update()

    def _draw_grid(self, painter: QPainter, origin: tuple[int, int]):
        """Draw a grid aligned to the triangle right-angle point (origin)."""
        if not self.grid_enabled:
            return

        palette = self.palette()
        fg = palette.color(self.foregroundRole())

        # Minor grid (more transparent)
        minor = QPen(fg, 1)
        minor_color = minor.color()
        minor_color.setAlpha(35)
        minor.setColor(minor_color)

        # Major grid (less transparent)
        major = QPen(fg, 1)
        major_color = major.color()
        major_color.setAlpha(70)
        major.setColor(major_color)

        w, h = self.width(), self.height()
        step = max(8, int(self.grid_step_px))
        major_every = max(2, int(self.grid_major_every))

        origin_x, origin_y = origin

        # --- Vertical lines: x = origin_x + k*step ---
        # Draw to the right
        x = origin_x
        i = 0
        while x <= w:
            painter.setPen(major if (i % major_every == 0) else minor)
            painter.drawLine(x, 0, x, h)
            x += step
            i += 1

        # Draw to the left
        x = origin_x - step
        i = 1
        while x >= 0:
            painter.setPen(major if (i % major_every == 0) else minor)
            painter.drawLine(x, 0, x, h)
            x -= step
            i += 1

        # --- Horizontal lines: y = origin_y - k*step (up) and +k*step (down) ---
        # Draw upward
        y = origin_y
        i = 0
        while y >= 0:
            painter.setPen(major if (i % major_every == 0) else minor)
            painter.drawLine(0, y, w, y)
            y -= step
            i += 1

        # Draw downward
        y = origin_y + step
        i = 1
        while y <= h:
            painter.setPen(major if (i % major_every == 0) else minor)
            painter.drawLine(0, y, w, y)
            y += step
            i += 1

    def _compute_triangle_points(self, margin: int, base_y: int):
        """
        Compute triangle points for proportional right-triangle drawing.

        Returns
        -------
        (point_c, point_a, point_b, scale) where:
        - point_c: right angle (bottom-left)
        - point_a: bottom-right (along b)
        - point_b: top-left (along a)
        """
        w, _h = self.width(), self.height()
        a_val = float(self.result_a) if self.result_a is not None else 1.0
        b_val = float(self.result_b) if self.result_b is not None else 1.0

        avail_w = max(1, w - 2 * margin)
        avail_h = max(1, base_y - margin)

        scale = min(avail_w / b_val, avail_h / a_val)

        x0 = margin
        y0 = base_y

        point_c = (x0, y0)
        point_a = (x0 + int(b_val * scale), y0)
        point_b = (x0, y0 - int(a_val * scale))

        return point_c, point_a, point_b, scale

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        palette = self.palette()
        text_color = palette.color(self.foregroundRole())

        w, h = self.width(), self.height()
        margin = 40

        # Labels font (used also for metrics like ascent/height)
        painter.setFont(QFont("Arial", 12))
        painter.setPen(text_color)
        fm = painter.fontMetrics()

        def clamp(val: int, lo: int, hi: int) -> int:
            return max(lo, min(val, hi))

        def fmt(name: str, value) -> str:
            """Build label like 'b = 12.34' or just 'b' if value missing."""
            if not self.has_result or value is None:
                return name
            return f"{name} = {value:g}"

        def draw_centered_elided_text(x_center: int, y: int, text: str, max_width: int):
            """Draw elided text centered around x_center."""
            elided = fm.elidedText(text, Qt.ElideRight, max_width)
            text_w = fm.horizontalAdvance(elided)
            painter.drawText(x_center - text_w // 2, y, elided)

        def draw_elided_text(x: int, y: int, text: str, max_width: int):
            """Draw elided text anchored at x,y (baseline)."""
            elided = fm.elidedText(text, Qt.ElideRight, max_width)
            painter.drawText(x, y, elided)

        # Lift the base
        gap = max(6, self.grid_step_px // 2)
        needed = fm.height() + gap
        base_y = h - margin - min(needed, margin)

        # Decide whether we can draw a proportional right triangle
        can_draw_proportional = (
            self.has_result
            and self.is_right
            and self.result_a is not None
            and self.result_b is not None
            and self.result_c is not None
        )

        if can_draw_proportional:
            # Proportional right triangle using computed legs a,b
            point_c, point_a, point_b, _scale = self._compute_triangle_points(margin, base_y)
        else:
            # Placeholder: Right angle at bottom-left (C), isosceles legs
            point_c = (margin, base_y)
            point_a = (w - margin, base_y)
            point_b = (margin, margin)

        # Background grid aligned to the triangle right angle (point_c)
        self._draw_grid(painter, origin=point_c)

        # Triangle edges
        tri_pen = QPen(text_color, 2)
        painter.setPen(tri_pen)

        # Draw triangle edges
        painter.drawLine(point_c[0], point_c[1], point_a[0], point_a[1])  # base (leg b)
        painter.drawLine(point_c[0], point_c[1], point_b[0], point_b[1])  # vertical (leg a)
        painter.drawLine(point_b[0], point_b[1], point_a[0], point_a[1])  # hypotenuse (c)

        # Right-angle marker at C, scaled to triangle size
        leg_w = abs(point_a[0] - point_c[0])  # b in pixels (int)
        leg_h = abs(point_c[1] - point_b[1])  # a in pixels (int)
        min_leg = min(leg_w, leg_h)

        # Marker must not exceed 1/4 of the smallest leg
        ra_cap = max(3, min_leg // 4)
        scaled = int(0.12 * min_leg)
        ra = max(3, min(18, scaled, ra_cap))

        ra_pen = QPen(text_color, 3)
        painter.setPen(ra_pen)

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

        # --- b label: MUST be BELOW the b-line ---
        b_text = fmt("b", self.result_b)

        line_y = mid_ca[1]
        b_y = line_y + gap + fm.ascent()
        b_y = clamp(b_y, margin + fm.ascent(), h - margin // 2)

        b_max_left = mid_ca[0] - 5
        b_max_right = w - 5 - mid_ca[0]
        b_max_w = max(60, 2 * min(b_max_left, b_max_right))

        draw_centered_elided_text(mid_ca[0], b_y, b_text, max_width=b_max_w)

        # --- c label: anchored near midpoint (do not center) to avoid overlapping the slanted side ---
        c_text = fmt("c", self.result_c)
        c_x = clamp(mid_ba[0] + 10, 5, w - margin)
        c_y = clamp(mid_ba[1] - 10, margin, h - 5)
        draw_elided_text(c_x, c_y, c_text, max_width=w - c_x - 5)

        # --- a label: vertical text along the left leg (better for long values), centered ---
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
    - Show one computed output field only in CALCULATE mode.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pythagoras Tool")
        self.resize(720, 520)

        # Fonts
        self.output_font = QFont("Monospace")
        self.output_font.setStyleHint(QFont.Monospace)

        # Styles (neutral, theme-independent)
        self.output_field_style = """
        QLineEdit {
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #6a6a6a;
            border-radius: 6px;
            padding: 6px 10px;
            font-weight: 600;
        }
        QLineEdit:focus {
            border: 1px solid #8fb2ff;
        }
        """

        self.output_label_style = """
        QLabel {
            font-weight: 600;
        }
        """

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

        # --- Computed output field (shown only after a successful CALCULATE) ---
        output_row = QHBoxLayout()
        output_row.setSpacing(8)

        self.computed_out_label = QLabel("—")
        self.computed_out_label.setStyleSheet(self.output_label_style)
        output_row.addWidget(self.computed_out_label)

        self.computed_out = self._create_output_field()
        output_row.addWidget(self.computed_out)

        output_row.setStretchFactor(self.computed_out, 1)

        self.output_container = QWidget()
        self.output_container.setLayout(output_row)
        self.output_container.setVisible(False)
        layout.addWidget(self.output_container)

        # Action button
        self.action_button = QPushButton("—")
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self.on_action_clicked)
        input_row.addWidget(self.action_button)

        layout.addLayout(input_row)

        # When True, input changes must NOT overwrite the last result message.
        self._showing_result = False

    def _create_output_field(self) -> QLineEdit:
        """Create a read-only output field for the computed value."""
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFont(self.output_font)
        field.setStyleSheet(self.output_field_style)
        field.setFocusPolicy(Qt.StrongFocus)  # allow selection + Ctrl+C
        field.setMinimumWidth(140)
        return field

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

    def _hide_outputs(self) -> None:
        """Hide computed output container and clear its content."""
        self.output_container.setVisible(False)
        self.computed_out_label.setText("—")
        self.computed_out.clear()

    def _show_computed_output(self, key: str, value: float) -> None:
        """Show only the computed (missing) field in CALCULATE mode."""
        self.output_container.setVisible(True)
        self.computed_out_label.setText(f"{key}:")
        self.computed_out.setText(f"{value:g}")

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

    def on_action_clicked(self):
        """
        Read inputs -> call core -> show results.

        - Status shows ONLY core message, formatted into sentences-per-line.
        - Canvas displays exactly the values returned by core.
        - Inputs are cleared after the action.
        - Computed output field is shown only in CALCULATE mode (2 inputs).
        """
        # Detect mode BEFORE clearing inputs
        a_raw = self.a_edit.text().strip()
        b_raw = self.b_edit.text().strip()
        c_raw = self.c_edit.text().strip()
        filled = sum(bool(v) for v in (a_raw, b_raw, c_raw))

        a_txt = self._normalized_text(a_raw)
        b_txt = self._normalized_text(b_raw)
        c_txt = self._normalized_text(c_raw)

        result = core.proceed_data({"a": a_txt, "b": b_txt, "c": c_txt})

        # Lock status to keep result visible
        self._showing_result = True
        self.status_label.setText(self._sentence_wrap(result.message))

        # Canvas must display exactly what core returned
        if result.is_valid and result.a is not None and result.b is not None and result.c is not None:
            self.canvas.show_result(result.a, result.b, result.c, is_right=result.is_right)
        else:
            self.canvas.show_placeholder()

        # Show computed output only in CALCULATE mode (exactly 2 filled), never in VERIFY mode
        if filled == 2 and result.is_valid:
            if not a_raw and result.a is not None:
                self._show_computed_output("a", result.a)
            elif not b_raw and result.b is not None:
                self._show_computed_output("b", result.b)
            elif not c_raw and result.c is not None:
                self._show_computed_output("c", result.c)
            else:
                self._hide_outputs()
        else:
            self._hide_outputs()

        # Clear inputs after click
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
