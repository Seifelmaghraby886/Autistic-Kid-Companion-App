"""Settings re-uses the AI & Voice tab logic from ParentDashboard for now."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from ui.parent_dashboard import ParentDashboard


class SettingsScreen(ParentDashboard):
    """Alias; in this MVP Settings is one tab of ParentDashboard."""
    close_requested = Signal()
