"""ToolLauncher — maps AI's open_tool field to UI signals."""

from PySide6.QtCore import QObject, Signal


class ToolLauncher(QObject):
    open_calm_zone   = Signal()
    open_aac         = Signal(str)        # category hint (e.g. 'food')
    open_schedule    = Signal()
    open_tutorial    = Signal(str)        # tutorial key (e.g. 'brush_teeth')
    open_story       = Signal(str)        # theme hint
    open_game        = Signal()
    open_parent_pin  = Signal()
    open_safety      = Signal(dict)       # alert payload
    close_all_tools  = Signal()

    def dispatch(self, response: dict, child_input: str = ""):
        """Inspect validated AI JSON and emit the right signal. Returns the tool key."""
        tool = response.get("open_tool", "none")
        intent = response.get("intent", "")
        low = (child_input or "").lower()

        if tool == "calm_zone":
            self.open_calm_zone.emit()
        elif tool == "aac":
            category = self._aac_category_for(intent, low)
            self.open_aac.emit(category)
        elif tool == "schedule":
            self.open_schedule.emit()
        elif tool == "tutorial":
            self.open_tutorial.emit(self._tutorial_key_for(intent, low))
        elif tool == "story":
            self.open_story.emit("calm_night")
        elif tool == "game":
            self.open_game.emit()
        elif tool == "parent_pin":
            self.open_parent_pin.emit()
        elif tool == "safety":
            self.open_safety.emit({
                "alert_type": response.get("alert_type"),
                "summary": response.get("log_summary", ""),
                "reply": response.get("reply", ""),
            })
        else:
            return "none"
        return tool

    def _aac_category_for(self, intent, low_text):
        if intent == "need_food" or "akl" in low_text or "اكل" in low_text or "جعان" in low_text:
            return "food"
        if intent == "need_water" or "ashrab" in low_text or "ميه" in low_text or "مية" in low_text:
            return "water"
        if intent == "need_bathroom" or "حمام" in low_text:
            return "bathroom"
        if intent == "pain" or "وجع" in low_text or "ألم" in low_text:
            return "pain"
        if intent == "need_parent" or "ماما" in low_text or "بابا" in low_text:
            return "people"
        return "all"

    def _tutorial_key_for(self, intent, low_text):
        if any(k in low_text for k in ("brush","سناني","سنان","teeth")):
            return "brush_teeth"
        if any(k in low_text for k in ("wash","hand","ايدي","يديا","سيب")):
            return "wash_hands"
        return "brush_teeth"
