"""RobotBridge — emits simulated robot commands. Logs to DB; ready for real hardware."""

from PySide6.QtCore import QObject, Signal
from data import database as db


class RobotBridge(QObject):
    """Future: replace _send() with real serial/socket/HTTP to physical robot."""

    command_sent = Signal(dict)

    def __init__(self, child_id):
        super().__init__()
        self.child_id = child_id
        self.connected = False  # set True when real robot detected

    def send(self, command: dict):
        if not isinstance(command, dict) or not command:
            return
        try:
            db.log_robot_command(self.child_id, command)
        except Exception:
            pass
        self.command_sent.emit(command)
        self._send(command)

    def _send(self, command):
        """Real send. For now, just print. Replace with serial/MQTT/WebSocket later."""
        print(f"[Robot ←] {command}")
