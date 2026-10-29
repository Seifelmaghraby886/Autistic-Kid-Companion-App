"""
ARIA Visual Task Tutorials
Animated cartoon-style step-by-step ADL (Activities of Daily Living) lessons.
Each step shown with custom Qt animation + TTS narration.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QStackedWidget, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient, QRadialGradient
)

from ui.components import GlassCard, ARIAFaceWidget
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


# ═══════════════════════════════════════════════════════════════
#  Animated step illustrations
# ═══════════════════════════════════════════════════════════════
class TaskAnimation(QWidget):
    """Custom-drawn animated cartoon for a specific task step."""

    def __init__(self, task_type, step_index, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 280)
        self._task = task_type
        self._step = step_index
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def _tick(self):
        self._t += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Soft gradient bg
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(245, 250, 255))
        bg.setColorAt(1, QColor(230, 240, 255))
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 18, 18)
        painter.fillPath(path, bg)
        painter.setPen(QPen(QColor(0, 191, 168, 80), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Dispatch to task-specific drawer
        method = f"_draw_{self._task}_{self._step}"
        if hasattr(self, method):
            getattr(self, method)(painter, w, h)
        else:
            self._draw_default(painter, w, h)

    def _draw_default(self, p, w, h):
        p.setFont(QFont("Segoe UI Emoji", 64))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, "✨")

    # ─── BRUSHING TEETH (5 steps) ───────────────────────────
    def _draw_brush_teeth_0(self, p, w, h):
        # Step 1: Get toothbrush
        cx, cy = w/2, h/2
        # Brush handle
        p.setBrush(QColor(0, 191, 168))
        p.setPen(QPen(QColor(0, 145, 130), 2))
        p.drawRoundedRect(int(cx - 90), int(cy - 10 + math.sin(self._t)*4), 140, 20, 8, 8)
        # Bristles
        p.setBrush(QColor(255, 255, 255))
        p.drawRoundedRect(int(cx + 35), int(cy - 18 + math.sin(self._t)*4), 30, 36, 4, 4)
        # Bristle lines
        p.setPen(QPen(QColor(180, 200, 220), 1))
        for i in range(8):
            x = cx + 38 + i*3
            p.drawLine(int(x), int(cy - 16 + math.sin(self._t)*4), int(x), int(cy + 16 + math.sin(self._t)*4))
        # Hand emoji
        p.setFont(QFont("Segoe UI Emoji", 40))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 160, cy - 20, 60, 60), Qt.AlignCenter, "🤏")

    def _draw_brush_teeth_1(self, p, w, h):
        # Step 2: Add toothpaste
        cx, cy = w/2, h/2
        # Toothpaste tube
        p.setBrush(QColor(255, 200, 100))
        p.setPen(QPen(QColor(220, 160, 60), 2))
        p.drawRoundedRect(int(cx - 100), int(cy - 30), 80, 60, 10, 10)
        # Cap
        p.setBrush(QColor(220, 160, 60))
        p.drawRoundedRect(int(cx - 30), int(cy - 12), 14, 24, 4, 4)
        # Brush
        p.setBrush(QColor(0, 191, 168))
        p.drawRoundedRect(int(cx + 10), int(cy - 8), 100, 16, 6, 6)
        p.setBrush(QColor(255, 255, 255))
        p.drawRoundedRect(int(cx + 100), int(cy - 14), 24, 28, 4, 4)
        # Animated paste drop
        drop_y = cy - 8 - abs(math.sin(self._t * 2)) * 30
        p.setBrush(QColor(180, 220, 255))
        p.drawEllipse(QPointF(cx + 5, drop_y), 8, 12)

    def _draw_brush_teeth_2(self, p, w, h):
        # Step 3: Brush in circles
        cx, cy = w/2, h/2
        # Smiling mouth with teeth
        p.setBrush(QColor(255, 190, 190))
        p.drawEllipse(QPointF(cx, cy), 100, 60)
        # Teeth
        p.setBrush(QColor(255, 255, 255))
        for i in range(6):
            x = cx - 60 + i * 22
            p.drawRoundedRect(int(x), int(cy - 25), 18, 30, 3, 3)
        # Brush moving in circles
        angle = self._t * 2
        bx = cx + 40 * math.cos(angle)
        by = cy + 20 * math.sin(angle)
        p.setBrush(QColor(0, 191, 168))
        p.drawRoundedRect(int(bx - 30), int(by - 5), 50, 10, 4, 4)
        p.setBrush(QColor(255, 255, 255))
        p.drawRoundedRect(int(bx + 10), int(by - 8), 18, 16, 3, 3)
        # Sparkles
        for i in range(3):
            ang = self._t + i * 2
            sx = cx + 70 * math.cos(ang)
            sy = cy + 40 * math.sin(ang * 0.8)
            p.setPen(QColor(255, 215, 0))
            p.setFont(QFont("Segoe UI Emoji", 18))
            p.drawText(QRectF(sx - 12, sy - 12, 24, 24), Qt.AlignCenter, "✨")

    def _draw_brush_teeth_3(self, p, w, h):
        # Step 4: Spit and rinse
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 80))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 100, cy - 60, 100, 100), Qt.AlignCenter, "💧")
        # Sink
        p.setBrush(QColor(220, 230, 240))
        p.drawRoundedRect(int(cx + 10), int(cy - 30), 120, 80, 12, 12)
        # Faucet
        p.setBrush(QColor(180, 190, 200))
        p.drawRect(int(cx + 60), int(cy - 70), 16, 40)
        # Water stream
        p.setBrush(QColor(120, 200, 255))
        for i in range(3):
            offset = (self._t * 30 + i * 15) % 60
            p.drawEllipse(int(cx + 64), int(cy - 30 + offset), 8, 8)

    def _draw_brush_teeth_4(self, p, w, h):
        # Step 5: Smile! All done
        cx, cy = w/2, h/2
        # Big smile
        p.setBrush(QColor(255, 215, 100))
        p.drawEllipse(QPointF(cx, cy), 70, 70)
        # Eyes
        p.setBrush(QColor(40, 50, 70))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx - 22, cy - 15), 7, 7)
        p.drawEllipse(QPointF(cx + 22, cy - 15), 7, 7)
        # Smile
        p.setPen(QPen(QColor(40, 50, 70), 4, Qt.SolidLine, Qt.RoundCap))
        path = QPainterPath()
        path.moveTo(cx - 25, cy + 5)
        path.quadTo(cx, cy + 30, cx + 25, cy + 5)
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        # Sparkles
        for i in range(5):
            ang = self._t * 0.5 + i * 1.3
            sx = cx + 110 * math.cos(ang)
            sy = cy + 100 * math.sin(ang) - 30
            p.setFont(QFont("Segoe UI Emoji", 22))
            p.drawText(QRectF(sx - 15, sy - 15, 30, 30), Qt.AlignCenter, "⭐")

    # ─── HAND WASHING (5 steps) ──────────────────────────
    def _draw_wash_hands_0(self, p, w, h):
        cx, cy = w/2, h/2
        # Faucet
        p.setBrush(QColor(180, 190, 200))
        p.drawRect(int(cx - 8), int(cy - 80), 16, 50)
        p.drawRoundedRect(int(cx - 30), int(cy - 30), 60, 14, 4, 4)
        # Water
        p.setBrush(QColor(120, 200, 255))
        for i in range(4):
            offset = (self._t * 30 + i * 15) % 60
            p.drawEllipse(int(cx - 4), int(cy - 16 + offset), 8, 8)
        # Hands
        p.setFont(QFont("Segoe UI Emoji", 56))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 50, cy + 20, 100, 100), Qt.AlignCenter, "🤲")

    def _draw_wash_hands_1(self, p, w, h):
        cx, cy = w/2, h/2
        # Soap dispenser
        p.setBrush(QColor(255, 200, 220))
        p.drawRoundedRect(int(cx - 40), int(cy - 60), 80, 80, 10, 10)
        # Pump
        p.setBrush(QColor(220, 160, 200))
        p.drawRoundedRect(int(cx - 8), int(cy - 80), 16, 20, 4, 4)
        # Bubbles
        for i in range(6):
            ang = self._t + i
            bx = cx + 60 * math.cos(ang)
            by = cy + 30 * math.sin(ang) + 20
            p.setBrush(QColor(255, 255, 255, 200))
            p.setPen(QPen(QColor(150, 200, 255), 1))
            p.drawEllipse(QPointF(bx, by), 8 + math.sin(ang) * 3, 8 + math.sin(ang) * 3)
        # Hand
        p.setFont(QFont("Segoe UI Emoji", 48))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx + 50, cy + 10, 80, 80), Qt.AlignCenter, "✋")

    def _draw_wash_hands_2(self, p, w, h):
        # Rub hands together with bubbles
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 64))
        p.setPen(QColor(COLORS["text"]))
        offset = math.sin(self._t * 3) * 8
        p.drawText(QRectF(cx - 70 + offset, cy - 32, 70, 70), Qt.AlignCenter, "🫳")
        p.drawText(QRectF(cx + offset, cy - 32, 70, 70), Qt.AlignCenter, "🫴")
        # Bubbles around
        for i in range(12):
            ang = self._t * 0.5 + i * 0.5
            r = 90 + math.sin(self._t + i) * 20
            bx = cx + r * math.cos(ang)
            by = cy + r * 0.6 * math.sin(ang)
            p.setBrush(QColor(255, 255, 255, 220))
            p.setPen(QPen(QColor(120, 200, 255), 1))
            size = 6 + math.sin(self._t + i) * 4
            p.drawEllipse(QPointF(bx, by), size, size)

    def _draw_wash_hands_3(self, p, w, h):
        # Rinse with water
        cx, cy = w/2, h/2
        # Stream
        for i in range(8):
            offset = (self._t * 50 + i * 18) % 140
            p.setBrush(QColor(120, 200, 255, 200))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx, cy - 100 + offset), 12 - i * 0.3, 16 - i * 0.4)
        # Hands
        p.setFont(QFont("Segoe UI Emoji", 56))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 50, cy + 30, 100, 80), Qt.AlignCenter, "🤲")

    def _draw_wash_hands_4(self, p, w, h):
        # Dry with towel
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 80))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 50, cy - 40, 100, 100), Qt.AlignCenter, "🧻")
        # Sparkles
        for i in range(6):
            ang = self._t + i
            sx = cx + 100 * math.cos(ang)
            sy = cy + 80 * math.sin(ang)
            p.setFont(QFont("Segoe UI Emoji", 18))
            p.drawText(QRectF(sx - 12, sy - 12, 24, 24), Qt.AlignCenter, "✨")

    # ─── GETTING DRESSED (5 steps) ───────────────────────
    def _draw_dressed_0(self, p, w, h):
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 96))
        p.setPen(QColor(COLORS["text"]))
        bounce = math.sin(self._t * 2) * 10
        p.drawText(QRectF(cx - 60, cy - 60 + bounce, 120, 120), Qt.AlignCenter, "👕")
    def _draw_dressed_1(self, p, w, h):
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 96))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 60, cy - 60, 120, 120), Qt.AlignCenter, "👖")
    def _draw_dressed_2(self, p, w, h):
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 80))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 50, cy - 40, 100, 100), Qt.AlignCenter, "🧦")
    def _draw_dressed_3(self, p, w, h):
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 80))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 50, cy - 40, 100, 100), Qt.AlignCenter, "👟")
    def _draw_dressed_4(self, p, w, h):
        # Dressed and ready - a happy figure
        cx, cy = w/2, h/2
        p.setFont(QFont("Segoe UI Emoji", 100))
        p.setPen(QColor(COLORS["text"]))
        p.drawText(QRectF(cx - 60, cy - 60, 120, 120), Qt.AlignCenter, "🧒")
        # Sparkles
        for i in range(6):
            ang = self._t + i
            sx = cx + 90 * math.cos(ang)
            sy = cy + 80 * math.sin(ang)
            p.setFont(QFont("Segoe UI Emoji", 22))
            p.drawText(QRectF(sx - 15, sy - 15, 30, 30), Qt.AlignCenter, "⭐")


# ═══════════════════════════════════════════════════════════════
#  Tutorial definitions
# ═══════════════════════════════════════════════════════════════
TUTORIALS = {
    "brush_teeth": {
        "icon": "🪥",
        "title": {"en": "Brush Your Teeth", "ar": "اغسل سنانك", "de": "Zähne putzen"},
        "color": "#00BFA8",
        "video_id": "wKungLJesXk",  # YouTube — kids brushing teeth song
        "video_title": "Brushing Teeth Song for Kids",
        "steps": [
            {"en": "Pick up your toothbrush.",
             "ar": "خد فرشاية الأسنان.",
             "de": "Nimm deine Zahnbürste."},
            {"en": "Put a small amount of toothpaste on it.",
             "ar": "حط معجون أسنان قليل عليها.",
             "de": "Tu etwas Zahnpasta darauf."},
            {"en": "Brush gently in small circles for two minutes.",
             "ar": "اغسل سنانك بهدوء في دوائر صغيرة لمدة دقيقتين.",
             "de": "Putze sanft in kleinen Kreisen, zwei Minuten lang."},
            {"en": "Spit the toothpaste out and rinse with water.",
             "ar": "اتفل المعجون واغسل بالماية.",
             "de": "Spuck die Zahnpasta aus und spüle mit Wasser."},
            {"en": "Smile! Your teeth are clean and shiny.",
             "ar": "ابتسم! سنانك نضيفة ولامعة.",
             "de": "Lächle! Deine Zähne sind sauber und strahlend."},
        ],
    },
    "wash_hands": {
        "icon": "🧼",
        "title": {"en": "Wash Your Hands", "ar": "اغسل إيديك", "de": "Hände waschen"},
        "color": "#5CE5DC",
        "video_id": "dDHJW4r3elE",  # CDC kids handwashing
        "video_title": "Washing Hands Song",
        "steps": [
            {"en": "Turn on the water. Make it warm, not too hot.",
             "ar": "افتح الماية. خليها دافية، مش سخنة قوي.",
             "de": "Mach das Wasser an. Warm, nicht zu heiß."},
            {"en": "Put soap on your hands.",
             "ar": "حط صابون في إيديك.",
             "de": "Nimm Seife auf deine Hände."},
            {"en": "Rub your hands together for 20 seconds — count slowly.",
             "ar": "افرك إيديك مع بعض لمدة 20 ثانية — عد ببطء.",
             "de": "Reibe deine Hände 20 Sekunden lang — zähle langsam."},
            {"en": "Rinse all the soap off with water.",
             "ar": "اشطف كل الصابون بالماية.",
             "de": "Spüle die Seife mit Wasser ab."},
            {"en": "Dry your hands with a clean towel. All done!",
             "ar": "نشف إيديك بفوطة نضيفة. خلصت!",
             "de": "Trockne deine Hände mit einem sauberen Handtuch. Fertig!"},
        ],
    },
    "get_dressed": {
        "icon": "👕",
        "title": {"en": "Get Dressed", "ar": "البس هدومك", "de": "Anziehen"},
        "color": "#B388FF",
        "video_id": "vakkP9-iPSE",  # Getting dressed for kids
        "video_title": "Getting Dressed Song",
        "steps": [
            {"en": "Put on your shirt — head first, then arms.",
             "ar": "البس قميصك — الراس الأول، بعدين الإيدين.",
             "de": "Zieh dein T-Shirt an — erst der Kopf, dann die Arme."},
            {"en": "Put on your pants — one leg at a time.",
             "ar": "البس بنطلونك — رجل واحدة في كل مرة.",
             "de": "Zieh deine Hose an — ein Bein nach dem anderen."},
            {"en": "Put on your socks.",
             "ar": "البس شرابك.",
             "de": "Zieh deine Socken an."},
            {"en": "Put on your shoes. Don't forget to fasten them!",
             "ar": "البس جزمتك. متنساش تربطها!",
             "de": "Zieh deine Schuhe an. Vergiss nicht zu binden!"},
            {"en": "You did it! You're all dressed and ready.",
             "ar": "قدرت! انت ملبوس ومستعد.",
             "de": "Du hast es geschafft! Du bist angezogen und bereit."},
        ],
    },
    "tie_shoes": {
        "icon": "👟",
        "title": {"en": "Tie Your Shoes", "ar": "اربط جزمتك", "de": "Schuhe binden"},
        "color": "#FFB73D",
        "video_id": "X4PYTRiCEpQ",
        "video_title": "How to Tie Shoes — easy method",
        "steps": [
            {"en": "Cross the two laces to make an X.",
             "ar": "صلب الشريطتين كأنك بتعمل علامة إكس.",
             "de": "Kreuze die beiden Schnürsenkel zu einem X."},
            {"en": "Push one lace under the other and pull tight.",
             "ar": "ادخل شريطة تحت التانية واشد عليها.",
             "de": "Stecke einen Senkel unter den anderen und ziehe fest."},
            {"en": "Make a bunny ear loop with one lace.",
             "ar": "اعمل أذن أرنب بشريطة واحدة.",
             "de": "Forme eine Hasenohr-Schlaufe mit einem Senkel."},
            {"en": "Wrap the other lace around the bunny ear.",
             "ar": "لف الشريطة التانية حوالين الأذن.",
             "de": "Wickle den anderen Senkel um die Schlaufe."},
            {"en": "Pull through and tighten gently. Done!",
             "ar": "سحبها واشد بهدوء. خلصت!",
             "de": "Durchziehen und sanft festziehen. Fertig!"},
        ],
    },
    "use_bathroom": {
        "icon": "🚽",
        "title": {"en": "Use the Bathroom", "ar": "استخدم الحمام", "de": "Toilette"},
        "color": "#7B6EC4",
        "video_id": "F5d1tjp25xc",
        "video_title": "Potty Training Song",
        "steps": [
            {"en": "Walk to the bathroom calmly.",
             "ar": "روح للحمام بهدوء.",
             "de": "Gehe ruhig ins Badezimmer."},
            {"en": "Lift the toilet seat if you need to.",
             "ar": "ارفع غطاء التواليت لو محتاج.",
             "de": "Hebe den Toilettendeckel falls nötig."},
            {"en": "Use the toilet. Take your time.",
             "ar": "استخدم التواليت. خد وقتك.",
             "de": "Benutze die Toilette. Lass dir Zeit."},
            {"en": "Wipe carefully with toilet paper.",
             "ar": "نضف بهدوء بالورق.",
             "de": "Wische vorsichtig mit Toilettenpapier."},
            {"en": "Flush the toilet.",
             "ar": "اضغط السيفون.",
             "de": "Spüle die Toilette."},
            {"en": "Wash your hands with soap. Very important!",
             "ar": "اغسل إيديك بصابون. ده مهم جداً!",
             "de": "Wasche deine Hände mit Seife. Sehr wichtig!"},
        ],
    },
    "eat_meal": {
        "icon": "🍽️",
        "title": {"en": "Eat a Meal", "ar": "كل أكلتك", "de": "Mahlzeit essen"},
        "color": "#FF8B5C",
        "video_id": "RBgcN9lrZ3g",
        "video_title": "Table Manners for Kids",
        "steps": [
            {"en": "Sit at the table calmly.",
             "ar": "اقعد على الترابيزة بهدوء.",
             "de": "Setze dich ruhig an den Tisch."},
            {"en": "Use a fork or spoon. Take small bites.",
             "ar": "استخدم الشوكة أو الملعقة. كل لقم صغيرة.",
             "de": "Nimm Gabel oder Löffel. Nimm kleine Bissen."},
            {"en": "Chew slowly with your mouth closed.",
             "ar": "اطحن الأكل بهدوء وبوقك مقفول.",
             "de": "Kaue langsam mit geschlossenem Mund."},
            {"en": "Drink water between bites.",
             "ar": "اشرب ماية بين اللقم.",
             "de": "Trinke Wasser zwischen den Bissen."},
            {"en": "Say 'please' and 'thank you'.",
             "ar": "قول 'لو سمحت' و 'شكراً'.",
             "de": "Sage 'bitte' und 'danke'."},
            {"en": "When done, ask to be excused.",
             "ar": "لما تخلص، استأذن.",
             "de": "Wenn fertig, frage ob du gehen darfst."},
        ],
    },
    "bedtime_routine": {
        "icon": "🌙",
        "title": {"en": "Bedtime Routine", "ar": "روتين النوم", "de": "Schlafenszeit"},
        "color": "#A695FF",
        "video_id": "rcXqXAg2EaQ",
        "video_title": "Bedtime Routine Song",
        "steps": [
            {"en": "Put your toys away.",
             "ar": "رتب لعبك.",
             "de": "Räume deine Spielsachen weg."},
            {"en": "Take a warm bath or shower.",
             "ar": "اعمل دش دافي.",
             "de": "Nimm ein warmes Bad oder eine Dusche."},
            {"en": "Brush your teeth carefully.",
             "ar": "اغسل سنانك بهدوء.",
             "de": "Putze gründlich deine Zähne."},
            {"en": "Put on your pajamas.",
             "ar": "البس بيجامتك.",
             "de": "Zieh deinen Schlafanzug an."},
            {"en": "Read a story or hear one from ARIA.",
             "ar": "اقرا قصة أو خلي أريا تحكيلك.",
             "de": "Lies eine Geschichte oder ARIA erzählt dir eine."},
            {"en": "Close your eyes. Goodnight!",
             "ar": "اقفل عينيك. تصبح على خير!",
             "de": "Schließe die Augen. Gute Nacht!"},
        ],
    },
    "school_morning": {
        "icon": "🎒",
        "title": {"en": "School Morning", "ar": "صباح المدرسة", "de": "Schultag-Morgen"},
        "color": "#FFB347",
        "video_id": "7CuZr1Bz3W4",
        "video_title": "Morning Routine for School",
        "steps": [
            {"en": "Wake up when the alarm rings.",
             "ar": "اصحى لما المنبه يرن.",
             "de": "Wache auf wenn der Wecker klingelt."},
            {"en": "Eat breakfast slowly.",
             "ar": "اتفطر بهدوء.",
             "de": "Frühstücke in Ruhe."},
            {"en": "Brush teeth, wash face.",
             "ar": "اغسل سنانك ووشك.",
             "de": "Zähne putzen, Gesicht waschen."},
            {"en": "Get dressed in your school uniform.",
             "ar": "البس ملابس المدرسة.",
             "de": "Zieh deine Schuluniform an."},
            {"en": "Pack your bag. Check your schedule.",
             "ar": "حضر شنطتك. اتأكد من جدولك.",
             "de": "Pack deine Tasche. Schau auf den Stundenplan."},
            {"en": "Walk to the door. Time for school!",
             "ar": "اطلع للباب. وقت المدرسة!",
             "de": "Geh zur Tür. Zeit für die Schule!"},
        ],
    },
    "cross_street": {
        "icon": "🚸",
        "title": {"en": "Cross the Street Safely", "ar": "اعدي الشارع بأمان", "de": "Straße überqueren"},
        "color": "#FF6B7E",
        "video_id": "SDQqDFL7NV0",
        "video_title": "Road Safety for Kids",
        "steps": [
            {"en": "Stop at the curb. Don't step into the road yet.",
             "ar": "وقف عند الرصيف. متنزلش الشارع لسه.",
             "de": "Halte am Bordstein. Geh noch nicht auf die Straße."},
            {"en": "Look left.",
             "ar": "بص شمال.",
             "de": "Schau nach links."},
            {"en": "Look right.",
             "ar": "بص يمين.",
             "de": "Schau nach rechts."},
            {"en": "Look left again.",
             "ar": "بص شمال تاني.",
             "de": "Schau wieder nach links."},
            {"en": "Listen for cars too.",
             "ar": "اسمع الصوت كمان.",
             "de": "Hör auch auf Autos."},
            {"en": "If no cars are coming, walk across. Don't run.",
             "ar": "لو مفيش عربيات، اعدي ماشي. متجريش.",
             "de": "Wenn keine Autos kommen, gehe rüber. Nicht rennen."},
        ],
    },
}


class TutorialPlayer(QWidget):
    completed = Signal()

    def __init__(self, task_key, child_id, parent=None):
        super().__init__(parent)
        self._task_key = task_key
        self._child_id = child_id
        self._child = db.get_child(child_id) or {}
        self._lang = self._child.get("language", "en")
        self._tutorial = TUTORIALS[task_key]
        self._step = 0
        self._auto_advance = True
        self._build_ui()
        self._show_step()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Header
        title_text = self._tutorial["title"].get(self._lang, self._tutorial["title"]["en"])
        title = QLabel(f"{self._tutorial['icon']}  {title_text}")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(title)

        # Progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, len(self._tutorial["steps"]))
        self._progress_bar.setValue(1)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(8)
        layout.addWidget(self._progress_bar)

        # Animation card
        anim_card = GlassCard(self, radius=22)
        anim_layout = QVBoxLayout(anim_card)
        anim_layout.setContentsMargins(20, 18, 20, 18)
        self._anim_widget = TaskAnimation(self._task_key, 0, self)
        anim_layout.addWidget(self._anim_widget)

        # Step label
        self._step_label = QLabel("")
        self._step_label.setAlignment(Qt.AlignCenter)
        self._step_label.setWordWrap(True)
        self._step_label.setStyleSheet(f"""
            font-size: 18px; font-weight: 700;
            color: {COLORS['text']}; padding: 12px;
        """)
        anim_layout.addWidget(self._step_label)

        # Step counter
        self._counter_label = QLabel("Step 1 of 5")
        self._counter_label.setAlignment(Qt.AlignCenter)
        self._counter_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        anim_layout.addWidget(self._counter_label)
        layout.addWidget(anim_card)

        # Controls
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self._prev_btn = QPushButton("← Previous")
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 11px 22px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
            QPushButton:disabled {{ opacity: 0.4; }}
        """)
        self._prev_btn.clicked.connect(self._prev)

        self._read_btn = QPushButton("🔊  Read Aloud")
        self._read_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(179,136,255,0.15); color: #6B4EBF;
                border: 1.5px solid #B388FF; border-radius: 12px;
                padding: 11px 22px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(179,136,255,0.30); }}
        """)
        self._read_btn.clicked.connect(self._read_step)

        self._next_btn = QPushButton("Next →")
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:1 #00E5FF);
                color: white; border: none; border-radius: 12px;
                padding: 11px 26px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #5CE5DC; }}
        """)
        self._next_btn.clicked.connect(self._next)

        # Watch Video button (only if tutorial has a video_id)
        if self._tutorial.get("video_id"):
            self._video_btn = QPushButton(f"▶  Watch Video")
            self._video_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #FF6BC4, stop:1 #B388FF);
                    color: white; border: none; border-radius: 12px;
                    padding: 11px 22px; font-size: 13px; font-weight: 700;
                }}
                QPushButton:hover {{ background: #FF98D8; }}
            """)
            self._video_btn.clicked.connect(self._open_video)
        else:
            self._video_btn = None

        ctrl_row.addWidget(self._prev_btn)
        ctrl_row.addWidget(self._read_btn)
        if self._video_btn:
            ctrl_row.addWidget(self._video_btn)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self._next_btn)
        layout.addLayout(ctrl_row)

    def _open_video(self):
        """Open embedded YouTube video player."""
        video_id = self._tutorial.get("video_id")
        if not video_id:
            return
        try:
            from ui.video_player import YouTubePlayerDialog
            dlg = YouTubePlayerDialog(
                video_id,
                self._tutorial.get("video_title", "Tutorial Video"),
                parent=self
            )
            dlg.exec()
        except Exception as e:
            print(f"[Video player error: {e}]")
            # Fallback: open in browser
            import webbrowser
            webbrowser.open(f"https://www.youtube.com/watch?v={video_id}")

    def _show_step(self):
        steps = self._tutorial["steps"]
        text = steps[self._step].get(self._lang, steps[self._step]["en"])
        self._step_label.setText(text)
        self._counter_label.setText(f"Step {self._step + 1} of {len(steps)}")
        self._progress_bar.setValue(self._step + 1)
        self._prev_btn.setEnabled(self._step > 0)
        self._next_btn.setText("Done ✓" if self._step == len(steps) - 1 else "Next →")

        # Replace animation widget
        old = self._anim_widget
        self._anim_widget = TaskAnimation(self._task_key, self._step, self)
        old.parent().layout().replaceWidget(old, self._anim_widget)
        old.deleteLater()

        # Auto-narrate
        QTimer.singleShot(300, self._read_step)

    def _read_step(self):
        text = self._step_label.text()
        if text:
            try:
                from speech.tts_engine import speak
                speak(text, self._child_id, style="very_slow")
            except Exception:
                pass

    def _next(self):
        if self._step < len(self._tutorial["steps"]) - 1:
            self._step += 1
            self._show_step()
        else:
            self.completed.emit()

    def _prev(self):
        if self._step > 0:
            self._step -= 1
            self._show_step()


# ═══════════════════════════════════════════════════════════════
#  Tutorials Library Screen
# ═══════════════════════════════════════════════════════════════
class TaskTutorialsScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child = db.get_child(child_id) or {}
        self.setStyleSheet(MAIN_STYLE)
        self._stack = QStackedWidget(self)
        ml = QVBoxLayout(self)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.addWidget(self._stack)
        self._stack.addWidget(self._build_lobby())

    def _build_lobby(self):
        w = QWidget()
        self._bg = MeshBackground(w, intensity=0.5)
        self._bg.lower()

        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        back_btn.clicked.connect(self.go_back.emit)
        title = QLabel("📺 Visual Task Tutorials")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Animated step-by-step guides for daily tasks")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn); hdr.addSpacing(20)
        col = QVBoxLayout(); col.addWidget(title); col.addWidget(sub)
        hdr.addLayout(col); hdr.addStretch()
        layout.addLayout(hdr)

        # Tutorial cards
        grid_w = QWidget()
        grid_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_w)
        grid.setSpacing(16)

        lang = self._child.get("language", "en")
        for i, (key, tut) in enumerate(TUTORIALS.items()):
            card = GlassCard(self, radius=22, hover_lift=True)
            card.setMinimumHeight(160)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(24, 20, 24, 18)
            cl.setSpacing(8)

            icon_lbl = QLabel(tut["icon"])
            icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")
            title_lbl = QLabel(tut["title"].get(lang, tut["title"]["en"]))
            title_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text']}; background: transparent;")
            steps_lbl = QLabel(f"{len(tut['steps'])} steps")
            steps_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']}; background: transparent;")

            cl.addWidget(icon_lbl)
            cl.addWidget(title_lbl)
            cl.addWidget(steps_lbl)
            cl.addStretch()

            play_btn = QPushButton("▶  Start Tutorial")
            play_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {tut['color']}; color: white;
                    border: none; border-radius: 12px;
                    padding: 9px 18px; font-size: 12px; font-weight: 700;
                }}
                QPushButton:hover {{ background: {tut['color']}AA; }}
            """)
            play_btn.clicked.connect(lambda checked, k=key: self._launch(k))
            cl.addWidget(play_btn)
            grid.addWidget(card, i // 3, i % 3)

        layout.addWidget(grid_w, 1)
        return w

    def _launch(self, key):
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(24, 20, 24, 20)
        back = QPushButton("← Back to Tutorials")
        back.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
                max-width: 200px;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        back.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        wl.addWidget(back)
        player = TutorialPlayer(key, self._child_id)
        wl.addWidget(player, 1)
        self._stack.addWidget(wrap)
        self._stack.setCurrentWidget(wrap)

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
