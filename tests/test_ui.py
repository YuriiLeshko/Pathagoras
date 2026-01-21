import pytest

from pathagoras import core
from pathagoras import ui_qt

@pytest.fixture
def window(qtbot):
    w = ui_qt.MainWindow()
    qtbot.addWidget(w)
    w.show()
    return w


def test_button_state_disabled_when_0_or_1_filled(window):
    assert window.action_button.isEnabled() is False
    assert window.action_button.text() == "—"

    window.a_edit.setText("3")
    assert window.action_button.isEnabled() is False
    assert window.action_button.text() == "—"


def test_button_state_calculate_when_2_filled(window):
    window.a_edit.setText("3")
    window.b_edit.setText("4")
    assert window.action_button.isEnabled() is True
    assert window.action_button.text() == "Calculate"


def test_button_state_verify_when_3_filled(window):
    window.a_edit.setText("3")
    window.b_edit.setText("4")
    window.c_edit.setText("5")
    assert window.action_button.isEnabled() is True
    assert window.action_button.text() == "Verify"


def test_click_calculate_normalizes_comma_and_shows_computed_output(window, qtbot, monkeypatch):
    calls = {}

    def fake_proceed_data(data):
        # check comma normalized to dot
        calls["data"] = dict(data)
        # simulate successful hypotenuse calculation (missing c)
        return core.TriangleData(a=3.5, b=4.0, c=5.315072906, is_valid=True, is_right=True, message="Hypotenuse calculated")

    monkeypatch.setattr(ui_qt.core, "proceed_data", fake_proceed_data)

    window.a_edit.setText("3,5")
    window.b_edit.setText("4")
    assert window.action_button.text() == "Calculate"

    qtbot.mouseClick(window.action_button, ui_qt.Qt.LeftButton)

    assert calls["data"]["a"] == "3.5"
    assert calls["data"]["b"] == "4"
    assert calls["data"]["c"] == ""

    # status shows core message
    assert "Hypotenuse calculated" in window.status_label.text()

    # inputs cleared
    assert window.a_edit.text() == ""
    assert window.b_edit.text() == ""
    assert window.c_edit.text() == ""

    # output shown and is for missing c
    assert window.output_container.isVisible() is True
    assert window.computed_out_label.text() == "c:"
    assert window.computed_out.text() != ""

    # canvas shows result
    assert window.canvas.has_result is True


def test_click_verify_hides_computed_output(window, qtbot, monkeypatch):
    def fake_proceed_data(_data):
        return core.TriangleData(a=3.0, b=4.0, c=5.0, is_valid=True, is_right=True, message="Input sorted: largest treated as hypotenuse. Triangle is RIGHT")

    monkeypatch.setattr(ui_qt.core, "proceed_data", fake_proceed_data)

    window.a_edit.setText("3")
    window.b_edit.setText("4")
    window.c_edit.setText("5")
    assert window.action_button.text() == "Verify"

    qtbot.mouseClick(window.action_button, ui_qt.Qt.LeftButton)

    assert window.output_container.isVisible() is False
    assert window.canvas.has_result is True
    assert "Triangle is RIGHT" in window.status_label.text()


def test_click_error_shows_placeholder_and_hides_output(window, qtbot, monkeypatch):
    def fake_proceed_data(_data):
        return core.TriangleData(is_valid=False, is_right=False, message="boom")

    monkeypatch.setattr(ui_qt.core, "proceed_data", fake_proceed_data)

    window.a_edit.setText("3")
    window.b_edit.setText("4")

    qtbot.mouseClick(window.action_button, ui_qt.Qt.LeftButton)

    assert "boom" in window.status_label.text()
    assert window.canvas.has_result is False
    assert window.output_container.isVisible() is False
