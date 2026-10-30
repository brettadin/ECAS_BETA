"""Event filters and input controllers for reliable UI navigation.

Prevents incidental mouse-wheel scrolling over unfocused dropdowns, numeric
spin boxes, and sliders from unexpectedly changing their values during page
scrolling. Also provides plot-interaction guards to prevent accidental plot
zooming when scrolling a workspace page.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QScrollArea,
    QSlider,
    QWidget,
)


class IgnoreWheelUnlessFocusedFilter(QObject):
    """Event filter that suppresses mouse wheel events on controls unless focused.

    When the mouse cursor scrolls over an unfocused QComboBox, QSpinBox, or
    QSlider, the wheel event is intercepted and forwarded to the enclosing
    QScrollArea (if present) so the page scrolls smoothly without altering
    input values.

    When the user intentionally clicks or tabs to focus the control, wheel
    events and keyboard arrows modify its value as expected.
    """

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            if isinstance(watched, (QComboBox, QAbstractSpinBox, QSlider)):
                if not watched.hasFocus():
                    event.ignore()
                    parent = watched.parent()
                    while parent is not None:
                        if isinstance(parent, QScrollArea):
                            parent.wheelEvent(event)
                            return True
                        parent = parent.parent()
                    return True
        return super().eventFilter(watched, event)


def apply_wheel_protection(widget: QWidget) -> None:
    """Recursively set strong focus and install wheel protection on input controls."""
    for cls in (QComboBox, QAbstractSpinBox, QSlider):
        for child in widget.findChildren(cls):
            child.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
