# -*- coding: utf-8 -*-
import sys
import os
import json
import random
import requests
from collections import Counter

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame,
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout,
    QStackedWidget, QSizePolicy, QLineEdit, QMessageBox,
    QGraphicsDropShadowEffect, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ============================================================
# Paths
# ============================================================
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
DATA_PATH = os.path.join(BASE_DIR, "data", "lotto_cache.json")
LOGO_PATH = os.path.join(BASE_DIR, "logo", "logo.png")


# ============================================================
# Styles
# ============================================================
APP_QSS = r"""
QMainWindow{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #071019, stop:1 #08362c);
}

QWidget{
    font-family:"Malgun Gothic","Segoe UI";
}

QLabel{
    color:#eaf0ff;
    font-size:13px;
}

QFrame#Sidebar{
    background:#030913;
}

QFrame#Content{
    background:transparent;
}

QFrame#Card{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f1b2a, stop:1 #0a3c31);
    border:1px solid rgba(255,255,255,0.06);
    border-radius:18px;
}

QLabel#CardTitle{
    font-size:16px;
    font-weight:800;
    color:white;
}

QLabel#BigNumber{
    font-size:28px;
    font-weight:800;
    color:#ffffff;
}

QLabel#SectionTitle{
    font-size:22px;
    font-weight:800;
    color:white;
}

QPushButton#NavBtn{
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.06);
    border-radius:14px;
    padding:14px 16px;
    text-align:left;
    font-size:14px;
    font-weight:700;
    color:white;
}
QPushButton#NavBtn:hover{
    background:rgba(46,201,150,0.10);
    border:1px solid rgba(120,255,210,0.20);
}
QPushButton#NavBtn:checked{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(46,201,150,0.18),
        stop:1 rgba(15,90,68,0.16)
    );
    border:1px solid rgba(120,255,210,0.28);
}

QPushButton#PrimaryBtn{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #27b587, stop:1 #178566);
    border:1px solid rgba(45,226,165,0.60);
    border-radius:12px;
    padding:10px 14px;
    font-size:13px;
    font-weight:700;
    color:white;
}
QPushButton#PrimaryBtn:hover{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #31c896, stop:1 #1a936f);
}
QPushButton#PrimaryBtn:pressed{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1f8f69, stop:1 #146b50);
}

QLabel#Muted{
    font-size:13px;
    color:rgba(255,255,255,0.74);
}

QLabel#StatValue{
    font-size:20px;
    font-weight:800;
    color:#2ec996;
}

QLabel#StatLabel{
    font-size:11px;
    font-weight:600;
    color:rgba(255,255,255,0.55);
}

QLabel#HistoryNum{
    font-size:12px;
    font-weight:800;
    color:#04140f;
    background:qradialgradient(
        cx:0.30, cy:0.25, radius:0.95,
        fx:0.30, fy:0.25,
        stop:0 #62f0c7,
        stop:0.45 #32c99a,
        stop:1 #11654c
    );
    border:1px solid rgba(120,255,210,0.60);
    border-radius:14px;
    min-width:28px;
    max-width:28px;
    min-height:28px;
    max-height:28px;
}

QLineEdit{
    background:rgba(255,255,255,0.07);
    border:1px solid rgba(255,255,255,0.10);
    border-radius:12px;
    padding:0 12px;
    color:white;
    font-size:13px;
    font-weight:600;
}

QScrollArea{
    border:none;
    background:transparent;
}

QScrollBar:vertical{
    background:rgba(255,255,255,0.04);
    width:6px;
    border-radius:3px;
}
QScrollBar::handle:vertical{
    background:rgba(46,201,150,0.40);
    border-radius:3px;
    min-height:24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{
    height:0;
}
"""


# ============================================================
# Helpers
# ============================================================
def ensure_parent_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def safe_load_cache():
    if not os.path.exists(DATA_PATH):
        ensure_parent_dir(DATA_PATH)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(data: dict):
    ensure_parent_dir(DATA_PATH)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_round(round_no: int):
    url = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"
    params = {"srchDir": "center", "srchLtEpsd": round_no}
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.dhlottery.co.kr/lt645/result"}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("data", {}).get("list", [])


def make_card(min_h=None):
    card = QFrame()
    card.setObjectName("Card")
    if min_h:
        card.setMinimumHeight(min_h)

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(28)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(0, 0, 0, 120))
    card.setGraphicsEffect(shadow)

    lay = QVBoxLayout(card)
    lay.setContentsMargins(18, 16, 18, 16)
    lay.setSpacing(10)
    return card, lay


def make_ball(n: int, size: int = 50):
    lbl = QLabel(str(n))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFixedSize(size, size)
    r = size // 2
    lbl.setStyleSheet(f"""
    QLabel{{
        background:qradialgradient(
            cx:0.30, cy:0.25, radius:0.95,
            fx:0.30, fy:0.25,
            stop:0 #62f0c7,
            stop:0.45 #32c99a,
            stop:1 #11654c
        );
        border:1px solid rgba(120,255,210,0.60);
        border-radius:{r}px;
        font-size:{max(10, size//3)}px;
        font-weight:800;
        color:#04140f;
    }}
    """)
    return lbl


def make_bonus_ball(n: int, size: int = 50):
    lbl = QLabel(str(n))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFixedSize(size, size)
    r = size // 2
    lbl.setStyleSheet(f"""
    QLabel{{
        background:qradialgradient(
            cx:0.30, cy:0.25, radius:0.95,
            fx:0.30, fy:0.25,
            stop:0 #ffd966,
            stop:0.45 #e6a817,
            stop:1 #a06800
        );
        border:1px solid rgba(255,210,80,0.70);
        border-radius:{r}px;
        font-size:{max(10, size//3)}px;
        font-weight:800;
        color:#2a1800;
    }}
    """)
    return lbl


def make_stat_mini(label: str, value: str):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(2)
    val_lbl = QLabel(value)
    val_lbl.setObjectName("StatValue")
    lbl_lbl = QLabel(label)
    lbl_lbl.setObjectName("StatLabel")
    v.addWidget(val_lbl, alignment=Qt.AlignCenter)
    v.addWidget(lbl_lbl, alignment=Qt.AlignCenter)
    return w


# ============================================================
# Donut Chart
# ============================================================
class DonutChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._labels = []
        self._values = []
        self._title = "Total Picks"
        self.fig = Figure(dpi=96)
        self.fig.patch.set_alpha(0.0)
        self.fig.patch.set_facecolor("none")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.canvas)

    def set_data(self, labels, values, title="Total Picks"):
        self._labels = labels
        self._values = list(values)
        self._title = title
        self._draw()

    def _draw(self):
        self.fig.clear()
        self.fig.patch.set_facecolor("none")

        labels = self._labels or ["No Data"]
        values = self._values if self._values and sum(self._values) > 0 else [1]
        colors = ["#FFD700", "#E6C200", "#C9A227", "#B8960B", "#9C7F00"]

        # 고배율/DPI 환경에서 중앙 텍스트가 도넛에 눌려 깨져 보이지 않도록
        # 도넛 홀을 키우고 중앙 텍스트 크기를 낮춘다.
        ax = self.fig.add_axes([0.03, 0.10, 0.44, 0.80])
        ax.set_facecolor("none")
        ax.set_aspect("equal")
        ax.axis("off")

        wedges, _ = ax.pie(
            values,
            startangle=90,
            colors=colors[:len(values)],
            wedgeprops=dict(width=0.32, edgecolor="none")
        )

        total = sum(self._values) if self._values else 0
        ax.text(
            0, 0.06, self._title,
            ha="center", va="center",
            fontsize=6.2, fontweight="bold", color="white"
        )
        ax.text(
            0, -0.10, f"{total:,}",
            ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="white"
        )

        lax = self.fig.add_axes([0.54, 0.14, 0.40, 0.72])
        lax.set_facecolor("none")
        lax.axis("off")

        y_positions = [0.86, 0.68, 0.50, 0.32, 0.14]
        for i, (lbl, w) in enumerate(zip(labels, wedges)):
            y = y_positions[i] if i < len(y_positions) else max(0.10, 0.86 - i * 0.16)
            rect = plt.Rectangle(
                (0.0, y - 0.04), 0.18, 0.08,
                color=w.get_facecolor(),
                transform=lax.transAxes,
                clip_on=False
            )
            lax.add_patch(rect)
            lax.text(
                0.26, y, lbl,
                va="center", ha="left",
                fontsize=7, fontweight="bold", color="white",
                transform=lax.transAxes
            )

        self.canvas.draw()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._values:
            self._draw()


# ============================================================
# Frequency Bar Chart
# ============================================================
class FrequencyBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._freq = None
        self.fig = Figure(dpi=96)
        self.fig.patch.set_facecolor("none")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.canvas)

    def set_data(self, freq: Counter):
        self._freq = freq
        self._draw()

    def _draw(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("none")
        self.fig.patch.set_facecolor("none")

        numbers = list(range(1, 46))
        counts = [self._freq.get(n, 0) for n in numbers]

        if not any(counts):
            ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center",
                    color="white", fontsize=12, transform=ax.transAxes)
            self.canvas.draw()
            return

        max_c = max(counts)
        top5_idx = set(sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)[:5])

        colors = []
        for i, c in enumerate(counts):
            ratio = c / max_c if max_c > 0 else 0
            r = int(17 + ratio * (98 - 17))
            g = int(101 + ratio * (240 - 101))
            b = int(76 + ratio * (199 - 76))
            colors.append(f"#{r:02x}{g:02x}{b:02x}")

        bars = ax.bar(numbers, counts, color=colors, width=0.72, linewidth=0)

        # 모든 막대 위에 번호 표시 (홀/짝 교대로 높이 오프셋 적용해 겹침 방지)
        for i, (num, cnt) in enumerate(zip(numbers, counts)):
            is_top = i in top5_idx
            if is_top:
                bars[i].set_edgecolor((1, 1, 1, 0.7))
                bars[i].set_linewidth(1.4)
            # 홀수 인덱스는 약간 더 높이 표시해서 겹침 방지
            offset = max_c * 0.04 if i % 2 == 0 else max_c * 0.10
            ax.text(num, cnt + offset, str(num),
                    ha="center", va="bottom",
                    fontsize=6, fontweight="bold" if is_top else "normal",
                    color="#78ffd2" if is_top else (1, 1, 1, 0.65))

        ax.set_xlim(0.2, 45.8)
        ax.set_ylim(0, max_c * 1.30)
        ax.set_xticks([])
        ax.tick_params(axis="y", colors=(1, 1, 1, 0.35), labelsize=7)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color((1, 1, 1, 0.10))
        ax.spines["bottom"].set_color((1, 1, 1, 0.10))

        self.fig.tight_layout(pad=0.3)
        self.canvas.draw()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._freq is not None:
            self._draw()


# ============================================================
# Odd/Even Pie Chart
# ============================================================
class OddEvenChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._odd = 0
        self._even = 0
        self.fig = Figure(dpi=96)
        self.fig.patch.set_facecolor("none")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background:transparent;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.canvas)

    def set_data(self, odd: int, even: int):
        self._odd = odd
        self._even = even
        self._draw()

    def _draw(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("none")
        ax.set_aspect("equal")

        odd, even = self._odd, self._even
        total = odd + even
        if total == 0:
            odd, even, total = 1, 1, 2

        colors = ["#2ec996", "#e6a817"]
        wedges, _ = ax.pie(
            [odd, even], startangle=90, colors=colors,
            wedgeprops=dict(width=0.40, edgecolor="none")
        )

        odd_pct = odd / total * 100
        even_pct = even / total * 100

        ax.text(0, 0.12, "홀", ha="center", va="center",
                fontsize=8, fontweight="700", color="#2ec996")
        ax.text(0, -0.12, "짝", ha="center", va="center",
                fontsize=8, fontweight="700", color="#e6a817")
        ax.text(0, 0, f"{odd_pct:.0f}:{even_pct:.0f}",
                ha="center", va="center", fontsize=7, color="white",
                fontweight="800")

        self.canvas.draw()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._odd or self._even:
            self._draw()


# ============================================================
# Main App
# ============================================================
class LottoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = safe_load_cache()
        self.setWindowTitle("FortunaPick")
        self.resize(1400, 860)
        self.init_ui()

    # -----------------------------
    # Data helpers
    # -----------------------------
    def get_latest_round(self):
        if not self.data:
            return 0
        return max(int(k) for k in self.data.keys())

    def number_frequency(self):
        c = Counter()
        for r in self.data.values():
            nums = r.get("numbers") or []
            c.update(nums)
        return c

    def most_common_by_position(self):
        pos_counter = [Counter() for _ in range(6)]
        for r in self.data.values():
            nums = r.get("numbers") or []
            if len(nums) != 6:
                continue
            for i, n in enumerate(nums):
                pos_counter[i].update([n])
        result = []
        for c in pos_counter:
            if not c:
                result.append(0)
                continue
            num, _ = c.most_common(1)[0]
            result.append(num)
        return result

    def decade_distribution(self):
        bins = [0, 0, 0, 0, 0]
        for r in self.data.values():
            for n in (r.get("numbers") or []):
                if 1 <= n <= 10: bins[0] += 1
                elif 11 <= n <= 20: bins[1] += 1
                elif 21 <= n <= 30: bins[2] += 1
                elif 31 <= n <= 40: bins[3] += 1
                elif 41 <= n <= 45: bins[4] += 1
        labels = ["1-10", "11-20", "21-30", "31-40", "41-45"]
        return labels, bins

    def odd_even_stats(self):
        odd = even = 0
        for r in self.data.values():
            for n in (r.get("numbers") or []):
                if n % 2 == 1:
                    odd += 1
                else:
                    even += 1
        return odd, even

    def odd_even_per_draw_distribution(self):
        """Returns Counter of (odd_count) per draw (0~6 odd per draw)"""
        dist = Counter()
        for r in self.data.values():
            nums = r.get("numbers") or []
            if len(nums) != 6:
                continue
            odd_count = sum(1 for n in nums if n % 2 == 1)
            dist[odd_count] += 1
        return dist

    def consecutive_pattern_stats(self):
        """Returns: total draws, draws with at least one consecutive pair, max streak seen"""
        total = 0
        with_consec = 0
        max_streak = 0
        for r in self.data.values():
            nums = sorted(r.get("numbers") or [])
            if len(nums) != 6:
                continue
            total += 1
            streak = 1
            cur_max = 1
            has_consec = False
            for i in range(1, len(nums)):
                if nums[i] == nums[i-1] + 1:
                    streak += 1
                    cur_max = max(cur_max, streak)
                    has_consec = True
                else:
                    streak = 1
            if has_consec:
                with_consec += 1
            max_streak = max(max_streak, cur_max)
        return total, with_consec, max_streak

    def get_recent_draws(self, n=8):
        """Returns last n draws sorted descending by round"""
        if not self.data:
            return []
        sorted_rounds = sorted(self.data.keys(), key=lambda x: int(x), reverse=True)
        result = []
        for k in sorted_rounds[:n]:
            entry = self.data[k].copy()
            entry["round"] = int(k)
            result.append(entry)
        return result

    def generate_numbers(self):
        nums = random.sample(range(1, 46), 6)
        nums.sort()
        return nums

    # -----------------------------
    # UI
    # -----------------------------
    def init_ui(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(160)
        side_lay = QVBoxLayout(sidebar)
        side_lay.setContentsMargins(18, 18, 18, 18)
        side_lay.setSpacing(14)
        side_lay.setAlignment(Qt.AlignTop)

        brand_wrap = QWidget()
        brand_wrap_lay = QVBoxLayout(brand_wrap)
        brand_wrap_lay.setContentsMargins(0, 0, 0, 0)
        brand_wrap_lay.setSpacing(10)
        brand_wrap_lay.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        logo_lbl = QLabel()
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH)
            logo_lbl.setPixmap(pix.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_lbl.setText("◉")
            logo_lbl.setStyleSheet("font-size:22px; font-weight:900; color:#78ffd2;")
        logo_lbl.setFixedSize(56, 56)
        logo_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        brand_lbl = QLabel("FortunaPick")
        brand_lbl.setStyleSheet("font-size:30px; font-weight:900; letter-spacing:0px; color:white;")
        brand_lbl.setWordWrap(False)
        brand_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        brand_wrap_lay.addWidget(logo_lbl, alignment=Qt.AlignLeft)
        brand_wrap_lay.addWidget(brand_lbl, alignment=Qt.AlignLeft)
        side_lay.addWidget(brand_wrap)
        side_lay.addSpacing(12)

        self.btn_dash = QPushButton("Dashboard")
        self.btn_gen = QPushButton("Generator")
        self.btn_cfg = QPushButton("Config")

        for b in (self.btn_dash, self.btn_gen, self.btn_cfg):
            b.setObjectName("NavBtn")
            b.setCheckable(True)
            b.setFixedHeight(90)

        self.btn_dash.clicked.connect(lambda: self.set_page(0))
        self.btn_gen.clicked.connect(lambda: self.set_page(1))
        self.btn_cfg.clicked.connect(lambda: self.set_page(2))

        side_lay.addWidget(self.btn_dash)
        side_lay.addWidget(self.btn_gen)
        side_lay.addWidget(self.btn_cfg)
        side_lay.addStretch(1)

        content = QFrame()
        content.setObjectName("Content")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)

        self.pages = QStackedWidget()
        self.page_dashboard = self.build_dashboard_page()
        self.page_generator = self.build_generator_page()
        self.page_config = self.build_config_page()

        self.pages.addWidget(self.page_dashboard)
        self.pages.addWidget(self.page_generator)
        self.pages.addWidget(self.page_config)

        content_lay.addWidget(self.pages)

        root.addWidget(sidebar)
        root.addWidget(content)

        self.setCentralWidget(central)
        self.set_page(0)

    def set_page(self, idx: int):
        self.pages.setCurrentIndex(idx)
        self.btn_dash.setChecked(idx == 0)
        self.btn_gen.setChecked(idx == 1)
        self.btn_cfg.setChecked(idx == 2)

    # -----------------------------
    # Dashboard Page
    # -----------------------------
    def build_dashboard_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner_widget = QWidget()
        layout = QVBoxLayout(inner_widget)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ── ROW 1: Number Trends + Range Distribution ──
        top_wrap = QHBoxLayout()
        top_wrap.setSpacing(16)

        trend_card, trend_layout = make_card(min_h=190)
        title = QLabel("Number Trends")
        title.setObjectName("CardTitle")
        trend_layout.addWidget(title)
        sub = QLabel("포지션별 최다 출현 번호")
        sub.setObjectName("Muted")
        trend_layout.addWidget(sub)

        self.trend_balls_row = QHBoxLayout()
        self.trend_balls_row.setSpacing(0)
        nums = self.most_common_by_position()
        nums = [n for n in nums if n] or [0, 0, 0, 0, 0, 0]
        for i, n in enumerate(nums):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignCenter)
            pos_lbl = QLabel(f"#{i+1}")
            pos_lbl.setStyleSheet("font-size:11px; font-weight:600; color:rgba(255,255,255,0.40);")
            pos_lbl.setAlignment(Qt.AlignCenter)
            ball = make_ball(n, size=62)
            col.addWidget(pos_lbl)
            col.addWidget(ball, 0, Qt.AlignCenter)
            self.trend_balls_row.addLayout(col, 1)

        trend_layout.addStretch(1)
        trend_layout.addLayout(self.trend_balls_row)
        trend_layout.addStretch(1)

        right_card, right_lay = make_card(min_h=210)
        chart_title = QLabel("Range Distribution")
        chart_title.setObjectName("CardTitle")
        right_lay.addWidget(chart_title)
        self.donut = DonutChart()
        self.donut.setMinimumSize(200, 150)
        labels, values = self.decade_distribution()
        self.donut.set_data(labels, values, title="Total Picks")
        right_lay.addWidget(self.donut, 1)

        top_wrap.addWidget(trend_card, 5)
        top_wrap.addWidget(right_card, 4)
        layout.addLayout(top_wrap)

        # ── ROW 2: Latest Round + Latest Numbers + Top Numbers ──
        mid_wrap = QHBoxLayout()
        mid_wrap.setSpacing(16)

        c1, l1 = make_card(min_h=130)
        t1 = QLabel("Latest Round")
        t1.setObjectName("CardTitle")
        l1.addWidget(t1)
        self.latest_round_value = QLabel(str(self.get_latest_round()))
        self.latest_round_value.setObjectName("BigNumber")
        l1.addStretch(1)
        l1.addWidget(self.latest_round_value, alignment=Qt.AlignLeft | Qt.AlignBottom)

        c_mid, l_mid = make_card(min_h=130)
        t_mid = QLabel("Latest Winning Numbers")
        t_mid.setObjectName("CardTitle")
        l_mid.addWidget(t_mid)
        self.latest_win_row = QHBoxLayout()
        self.latest_win_row.setSpacing(8)
        self.latest_win_row.setAlignment(Qt.AlignLeft)
        l_mid.addLayout(self.latest_win_row)
        latest_draw = self.get_latest_draw_data()
        if latest_draw:
            for n in latest_draw.get("numbers", []):
                self.latest_win_row.addWidget(make_ball(n, size=42))
            bonus_lbl = QLabel("+")
            bonus_lbl.setStyleSheet("font-size:16px; font-weight:800; color:white;")
            self.latest_win_row.addWidget(bonus_lbl)
            self.latest_win_row.addWidget(make_bonus_ball(latest_draw.get("bonus", 0), size=42))
        l_mid.addStretch(1)

        c2, l2 = make_card(min_h=130)
        t2 = QLabel("Top Numbers")
        t2.setObjectName("CardTitle")
        l2.addWidget(t2)
        self.top_numbers_layout = QVBoxLayout()
        self.top_numbers_layout.setSpacing(5)
        l2.addLayout(self.top_numbers_layout)
        freq = self.number_frequency()
        if not freq:
            empty = QLabel("No cache data")
            empty.setObjectName("Muted")
            self.top_numbers_layout.addWidget(empty)
        else:
            top1_cnt = freq.most_common(1)[0][1]
            for num, cnt in freq.most_common(5):
                row_w = QHBoxLayout()
                row_w.setSpacing(6)
                num_lbl = QLabel(str(num))
                num_lbl.setFixedWidth(24)
                num_lbl.setStyleSheet("font-size:13px; font-weight:800; color:#2ec996;")
                bar_pct = cnt / top1_cnt if top1_cnt else 0
                bar_bg = QFrame()
                bar_bg.setFixedHeight(6)
                bar_bg.setStyleSheet("background:rgba(255,255,255,0.10); border-radius:3px;")
                bar_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                bar_fg = QFrame(bar_bg)
                bar_fg.setFixedHeight(6)
                bar_fg.setStyleSheet("background:#2ec996; border-radius:3px;")
                bar_fg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                # width will be set proportionally via stylesheet
                bar_fg.setFixedWidth(max(4, int(bar_pct * 80)))
                cnt_lbl = QLabel(f"{cnt}회")
                cnt_lbl.setFixedWidth(42)
                cnt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                cnt_lbl.setStyleSheet("font-size:11px; font-weight:600; color:rgba(255,255,255,0.65);")
                row_w.addWidget(num_lbl)
                row_w.addWidget(bar_bg)
                row_w.addWidget(cnt_lbl)
                self.top_numbers_layout.addLayout(row_w)
        l2.addStretch(1)

        mid_wrap.addWidget(c1, 1)
        mid_wrap.addWidget(c_mid, 2)
        mid_wrap.addWidget(c2, 1)
        layout.addLayout(mid_wrap)

        # ── ROW 3: Frequency Bar Chart (full width) ──
        freq_card, freq_lay = make_card(min_h=200)
        freq_title = QLabel("번호별 출현 빈도")
        freq_title.setObjectName("CardTitle")
        freq_lay.addWidget(freq_title)
        sub_freq = QLabel("1~45 전체 번호의 누적 출현 횟수 (밝을수록 고빈도)")
        sub_freq.setObjectName("Muted")
        freq_lay.addWidget(sub_freq)
        self.freq_bar = FrequencyBarChart()
        freq = self.number_frequency()
        self.freq_bar.set_data(freq)
        freq_lay.addWidget(self.freq_bar, 1)
        layout.addWidget(freq_card)

        # ── ROW 4: Odd/Even + Consecutive Pattern ──
        stat_row = QHBoxLayout()
        stat_row.setSpacing(16)

        # ── Odd/Even card ──
        oe_card, oe_lay = make_card(min_h=200)
        oe_title = QLabel("홀짝 비율 분석")
        oe_title.setObjectName("CardTitle")
        oe_lay.addWidget(oe_title)

        oe_inner = QHBoxLayout()
        oe_inner.setSpacing(12)

        self.oe_chart = OddEvenChart()
        odd, even = self.odd_even_stats()
        self.oe_chart.set_data(odd, even)
        oe_inner.addWidget(self.oe_chart, 1)

        oe_stats = QVBoxLayout()
        oe_stats.setSpacing(12)
        oe_stats.setAlignment(Qt.AlignVCenter)
        total_balls = odd + even
        odd_pct = odd / total_balls * 100 if total_balls > 0 else 0
        even_pct = even / total_balls * 100 if total_balls > 0 else 0

        # Per-draw distribution breakdown
        dist = self.odd_even_per_draw_distribution()
        most_common_oe = dist.most_common(1)[0] if dist else (0, 0)

        self.oe_odd_lbl = QLabel(f"{odd:,}")
        self.oe_odd_lbl.setObjectName("StatValue")
        oe_odd_sub = QLabel(f"홀수 ({odd_pct:.1f}%)")
        oe_odd_sub.setObjectName("StatLabel")

        self.oe_even_lbl = QLabel(f"{even:,}")
        self.oe_even_lbl.setObjectName("StatValue")
        self.oe_even_lbl.setStyleSheet("font-size:20px; font-weight:800; color:#e6a817;")
        oe_even_sub = QLabel(f"짝수 ({even_pct:.1f}%)")
        oe_even_sub.setObjectName("StatLabel")

        self.oe_common_lbl = QLabel(f"홀{most_common_oe[0]}개" if dist else "-")
        self.oe_common_lbl.setObjectName("StatValue")
        oe_common_sub = QLabel("가장 흔한 홀수 조합")
        oe_common_sub.setObjectName("StatLabel")

        for w in [self.oe_odd_lbl, oe_odd_sub, self.oe_even_lbl, oe_even_sub, self.oe_common_lbl, oe_common_sub]:
            oe_stats.addWidget(w)
        oe_stats.addStretch(1)

        oe_inner.addLayout(oe_stats, 1)
        oe_lay.addLayout(oe_inner)

        # ── Consecutive Pattern card ──
        cp_card, cp_lay = make_card(min_h=200)
        cp_title = QLabel("연속번호 패턴 분석")
        cp_title.setObjectName("CardTitle")
        cp_lay.addWidget(cp_title)

        total_draws, with_consec, max_streak = self.consecutive_pattern_stats()
        consec_pct = with_consec / total_draws * 100 if total_draws > 0 else 0
        no_consec_pct = 100 - consec_pct

        cp_grid = QGridLayout()
        cp_grid.setSpacing(14)

        def big_stat(val, lbl_text, color="#2ec996"):
            v_lbl = QLabel(str(val))
            v_lbl.setStyleSheet(f"font-size:26px; font-weight:800; color:{color};")
            v_lbl.setAlignment(Qt.AlignCenter)
            l_lbl = QLabel(lbl_text)
            l_lbl.setObjectName("StatLabel")
            l_lbl.setAlignment(Qt.AlignCenter)
            w = QWidget()
            vl = QVBoxLayout(w)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(4)
            vl.addWidget(v_lbl)
            vl.addWidget(l_lbl)
            return w

        self.cp_total_lbl = big_stat(total_draws, "전체 회차")
        self.cp_consec_lbl = big_stat(with_consec, "연속번호 포함 회차", "#2ec996")
        self.cp_pct_lbl = big_stat(f"{consec_pct:.1f}%", "연속번호 출현율", "#78ffd2")
        self.cp_max_lbl = big_stat(max_streak, "최장 연속 길이", "#ffd700")

        cp_grid.addWidget(self.cp_total_lbl, 0, 0)
        cp_grid.addWidget(self.cp_consec_lbl, 0, 1)
        cp_grid.addWidget(self.cp_pct_lbl, 1, 0)
        cp_grid.addWidget(self.cp_max_lbl, 1, 1)
        cp_lay.addLayout(cp_grid)

        # Mini bar for consecutive ratio
        ratio_wrap = QWidget()
        ratio_lay = QHBoxLayout(ratio_wrap)
        ratio_lay.setContentsMargins(0, 4, 0, 0)
        ratio_lay.setSpacing(0)

        bar_consec = QFrame()
        bar_consec.setFixedHeight(6)
        bar_consec.setStyleSheet("background:#2ec996; border-radius:3px;")
        bar_consec.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if total_draws > 0:
            bar_consec.setFixedWidth(max(1, int(consec_pct * 2)))

        bar_no = QFrame()
        bar_no.setFixedHeight(6)
        bar_no.setStyleSheet("background:rgba(255,255,255,0.12); border-radius:3px;")
        bar_no.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        ratio_lay.addWidget(bar_consec)
        ratio_lay.addWidget(bar_no)

        lbl_ratio = QLabel(f"연속포함 {consec_pct:.1f}% / 미포함 {no_consec_pct:.1f}%")
        lbl_ratio.setObjectName("Muted")
        lbl_ratio.setAlignment(Qt.AlignCenter)
        cp_lay.addWidget(ratio_wrap)
        cp_lay.addWidget(lbl_ratio)

        stat_row.addWidget(oe_card, 1)
        stat_row.addWidget(cp_card, 1)
        layout.addLayout(stat_row)

        # ── ROW 5: Recent N Draws History ──
        hist_card, hist_lay = make_card(min_h=180)
        hist_title = QLabel("최근 당첨번호 히스토리")
        hist_title.setObjectName("CardTitle")
        hist_lay.addWidget(hist_title)
        sub_hist = QLabel("최근 8회차")
        sub_hist.setObjectName("Muted")
        hist_lay.addWidget(sub_hist)

        self.history_vbox = QVBoxLayout()
        self.history_vbox.setSpacing(4)
        hist_lay.addLayout(self.history_vbox)
        self._populate_history()

        layout.addWidget(hist_card)

        # ── ROW 6: Quick Pick ──
        c3, l3 = make_card(min_h=140)
        t3 = QLabel("Quick Pick")
        t3.setObjectName("CardTitle")
        l3.addWidget(t3)
        self.quick_hint = QLabel("Press Generate to roll lucky numbers")
        self.quick_hint.setObjectName("Muted")
        l3.addWidget(self.quick_hint)
        self.quick_ball_row = QHBoxLayout()
        self.quick_ball_row.setSpacing(10)
        self.quick_ball_row.setAlignment(Qt.AlignLeft)
        l3.addLayout(self.quick_ball_row)
        btn = QPushButton("Generate")
        btn.setObjectName("PrimaryBtn")
        btn.setFixedHeight(40)
        btn.clicked.connect(self.on_quick_generate)
        l3.addStretch(1)
        l3.addWidget(btn)
        layout.addWidget(c3)

        layout.addStretch(1)

        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)
        return page

    def _populate_history(self):
        # Clear existing widgets
        while self.history_vbox.count():
            item = self.history_vbox.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        recent = self.get_recent_draws(8)
        if not recent:
            lbl = QLabel("데이터 없음")
            lbl.setObjectName("Muted")
            self.history_vbox.addWidget(lbl)
            return

        for draw in recent:
            row_w = QWidget()
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(0, 2, 0, 2)
            row_lay.setSpacing(10)

            round_lbl = QLabel(f"#{draw['round']}")
            round_lbl.setFixedWidth(50)
            round_lbl.setStyleSheet("font-size:12px; font-weight:700; color:rgba(255,255,255,0.55);")
            round_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_lay.addWidget(round_lbl)

            date_str = draw.get("date", "")
            if len(date_str) == 8:
                date_str = f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:]}"
            date_lbl = QLabel(date_str)
            date_lbl.setFixedWidth(82)
            date_lbl.setStyleSheet("font-size:11px; color:rgba(255,255,255,0.38);")
            date_lbl.setAlignment(Qt.AlignCenter)
            row_lay.addWidget(date_lbl)

            for n in draw.get("numbers", []):
                row_lay.addWidget(make_ball(n, size=28))

            plus = QLabel("+")
            plus.setStyleSheet("font-size:11px; font-weight:800; color:rgba(255,255,255,0.45);")
            row_lay.addWidget(plus)
            row_lay.addWidget(make_bonus_ball(draw.get("bonus", 0), size=28))
            row_lay.addStretch(1)

            self.history_vbox.addWidget(row_w)

    # -----------------------------
    # Data
    # -----------------------------
    def get_latest_draw_data(self):
        latest = self.get_latest_round()
        if latest <= 0:
            return None
        return self.data.get(str(latest))

    def on_update_cache_by_input(self):
        text = self.latest_round_input.text().strip()
        if not text.isdigit():
            QMessageBox.warning(self, "입력 오류", "최신 회차는 숫자로 입력해주세요.")
            return
        target_round = int(text)
        if target_round <= 0:
            QMessageBox.warning(self, "입력 오류", "1 이상의 회차를 입력해주세요.")
            return
        try:
            rows = fetch_round(target_round)
            if not rows:
                self.update_result_label.setText("조회 결과가 없습니다.")
                return
            added = updated = 0
            for item in rows:
                round_no = str(item["ltEpsd"])
                new_value = {
                    "date": item["ltRflYmd"],
                    "numbers": [item["tm1WnNo"], item["tm2WnNo"], item["tm3WnNo"],
                                item["tm4WnNo"], item["tm5WnNo"], item["tm6WnNo"]],
                    "bonus": item["bnsWnNo"]
                }
                if round_no in self.data:
                    updated += 1
                else:
                    added += 1
                self.data[round_no] = new_value
            save_cache(self.data)
            new_latest = self.get_latest_round()
            self.cache_latest_label.setText(f"현재 캐시 최신 회차: {new_latest}")
            self.update_result_label.setText(
                f"최신화 완료: 신규 {added}건 / 갱신 {updated}건 / 현재 최신 {new_latest}"
            )
            self.refresh_dashboard()
        except Exception as e:
            self.update_result_label.setText(f"업데이트 실패: {e}")
            QMessageBox.critical(self, "업데이트 실패", str(e))

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout(child_layout)

    def refresh_dashboard(self):
        if hasattr(self, "latest_round_value"):
            self.latest_round_value.setText(str(self.get_latest_round()))

        if hasattr(self, "top_numbers_layout"):
            self.clear_layout(self.top_numbers_layout)
            freq = self.number_frequency()
            if not freq:
                empty = QLabel("No cache data")
                empty.setObjectName("Muted")
                self.top_numbers_layout.addWidget(empty)
            else:
                top1_cnt = freq.most_common(1)[0][1]
                for num, cnt in freq.most_common(5):
                    row_w = QHBoxLayout()
                    row_w.setSpacing(6)
                    num_lbl = QLabel(str(num))
                    num_lbl.setFixedWidth(24)
                    num_lbl.setStyleSheet("font-size:13px; font-weight:800; color:#2ec996;")
                    bar_pct = cnt / top1_cnt if top1_cnt else 0
                    bar_bg = QFrame()
                    bar_bg.setFixedHeight(6)
                    bar_bg.setStyleSheet("background:rgba(255,255,255,0.10); border-radius:3px;")
                    bar_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    bar_fg = QFrame(bar_bg)
                    bar_fg.setFixedHeight(6)
                    bar_fg.setStyleSheet("background:#2ec996; border-radius:3px;")
                    bar_fg.setFixedWidth(max(4, int(bar_pct * 80)))
                    cnt_lbl = QLabel(f"{cnt}회")
                    cnt_lbl.setFixedWidth(42)
                    cnt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    cnt_lbl.setStyleSheet("font-size:11px; font-weight:600; color:rgba(255,255,255,0.65);")
                    row_w.addWidget(num_lbl)
                    row_w.addWidget(bar_bg)
                    row_w.addWidget(cnt_lbl)
                    self.top_numbers_layout.addLayout(row_w)

        if hasattr(self, "trend_balls_row"):
            self.clear_layout(self.trend_balls_row)
            nums = self.most_common_by_position()
            nums = [n for n in nums if n] or [0]*6
            for i, n in enumerate(nums):
                col = QVBoxLayout()
                col.setSpacing(4)
                col.setAlignment(Qt.AlignCenter)
                pos_lbl = QLabel(f"#{i+1}")
                pos_lbl.setStyleSheet("font-size:11px; font-weight:600; color:rgba(255,255,255,0.40);")
                pos_lbl.setAlignment(Qt.AlignCenter)
                col.addWidget(pos_lbl)
                col.addWidget(make_ball(n, size=62), 0, Qt.AlignCenter)
                self.trend_balls_row.addLayout(col, 1)

        if hasattr(self, "donut"):
            labels, values = self.decade_distribution()
            self.donut.set_data(labels, values, title="Total Picks")

        if hasattr(self, "freq_bar"):
            freq = self.number_frequency()
            self.freq_bar.set_data(freq)

        if hasattr(self, "oe_chart"):
            odd, even = self.odd_even_stats()
            self.oe_chart.set_data(odd, even)
            total_balls = odd + even
            odd_pct = odd / total_balls * 100 if total_balls > 0 else 0
            even_pct = even / total_balls * 100 if total_balls > 0 else 0
            self.oe_odd_lbl.setText(f"{odd:,}")
            self.oe_even_lbl.setText(f"{even:,}")
            dist = self.odd_even_per_draw_distribution()
            most_common_oe = dist.most_common(1)[0] if dist else (0, 0)
            self.oe_common_lbl.setText(f"홀{most_common_oe[0]}개" if dist else "-")

        if hasattr(self, "cp_total_lbl"):
            total_draws, with_consec, max_streak = self.consecutive_pattern_stats()
            consec_pct = with_consec / total_draws * 100 if total_draws > 0 else 0
            self.cp_total_lbl.findChildren(QLabel)[0].setText(str(total_draws))
            self.cp_consec_lbl.findChildren(QLabel)[0].setText(str(with_consec))
            self.cp_pct_lbl.findChildren(QLabel)[0].setText(f"{consec_pct:.1f}%")
            self.cp_max_lbl.findChildren(QLabel)[0].setText(str(max_streak))

        if hasattr(self, "latest_win_row"):
            self.clear_layout(self.latest_win_row)
            latest_draw = self.get_latest_draw_data()
            if latest_draw:
                for n in latest_draw.get("numbers", []):
                    self.latest_win_row.addWidget(make_ball(n, size=42))
                bonus_lbl = QLabel("+")
                bonus_lbl.setStyleSheet("font-size:16px; font-weight:800; color:white;")
                self.latest_win_row.addWidget(bonus_lbl)
                self.latest_win_row.addWidget(make_bonus_ball(latest_draw.get("bonus", 0), size=42))

        if hasattr(self, "history_vbox"):
            self._populate_history()

    # -----------------------------
    # Quick Pick
    # -----------------------------
    def on_quick_generate(self):
        self.quick_roll_step = 0
        if not hasattr(self, "quick_roll_timer"):
            self.quick_roll_timer = QTimer(self)
            self.quick_roll_timer.timeout.connect(self._roll_quick_numbers)
        self.quick_roll_timer.start(70)

    def _clear_layout_widgets(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _roll_quick_numbers(self):
        self.quick_roll_step += 1
        nums = self.generate_numbers()
        self._clear_layout_widgets(self.quick_ball_row)
        for n in nums:
            self.quick_ball_row.addWidget(make_ball(n, size=44))
        if self.quick_roll_step >= 12:
            self.quick_roll_timer.stop()
            final_nums = self.generate_numbers()
            self._clear_layout_widgets(self.quick_ball_row)
            for n in final_nums:
                self.quick_ball_row.addWidget(make_ball(n, size=48))
            self.quick_hint.setText("추천 번호가 생성되었습니다.")

    def _roll_generator_numbers(self):
        self.gen_roll_step += 1
        nums = self.generate_numbers()
        self._clear_layout_widgets(self.gen_row)
        for n in nums:
            self.gen_row.addWidget(make_ball(n, size=50))
        if self.gen_roll_step >= 12:
            self.gen_roll_timer.stop()
            final_nums = self.generate_numbers()
            self._clear_layout_widgets(self.gen_row)
            for n in final_nums:
                self.gen_row.addWidget(make_ball(n, size=56))
            self.gen_hint.setText("생성 완료")
            self.gen_last_label.setText("  ".join(map(str, final_nums)))

    # -----------------------------
    # Generator Page
    # -----------------------------
    def build_generator_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QLabel("Generator")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        card, cl = make_card(min_h=320)
        title = QLabel("Lucky Number Machine")
        title.setObjectName("CardTitle")
        cl.addWidget(title)

        self.gen_hint = QLabel("버튼을 누르면 추천 번호가 애니메이션으로 생성됩니다.")
        self.gen_hint.setObjectName("Muted")
        cl.addWidget(self.gen_hint)

        self.gen_row = QHBoxLayout()
        self.gen_row.setSpacing(10)
        self.gen_row.setAlignment(Qt.AlignLeft)
        cl.addLayout(self.gen_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        gen_btn = QPushButton("Generate Numbers")
        gen_btn.setObjectName("PrimaryBtn")
        gen_btn.setFixedHeight(42)
        gen_btn.clicked.connect(self.on_generate_page)
        btn_row.addWidget(gen_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("PrimaryBtn")
        clear_btn.setFixedHeight(42)
        clear_btn.clicked.connect(lambda: self._clear_layout_widgets(self.gen_row))
        btn_row.addWidget(clear_btn)

        cl.addStretch(1)
        cl.addLayout(btn_row)

        history_card, history_lay = make_card(min_h=120)
        history_title = QLabel("Last Generated Set")
        history_title.setObjectName("CardTitle")
        history_lay.addWidget(history_title)
        self.gen_last_label = QLabel("-")
        self.gen_last_label.setObjectName("Muted")
        history_lay.addWidget(self.gen_last_label)

        layout.addWidget(card)
        layout.addWidget(history_card)
        layout.addStretch(1)
        return page

    def on_generate_page(self):
        self.gen_roll_step = 0
        if not hasattr(self, "gen_roll_timer"):
            self.gen_roll_timer = QTimer(self)
            self.gen_roll_timer.timeout.connect(self._roll_generator_numbers)
        self.gen_roll_timer.start(70)

    # -----------------------------
    # Config Page
    # -----------------------------
    def build_config_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(22)

        header = QLabel("Config")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        card, cl = make_card(min_h=280)

        p = QLabel(f"Cache path:\n{DATA_PATH}")
        p.setStyleSheet("font-size:16px; font-weight:700; color:rgba(255,255,255,0.85);")
        p.setWordWrap(True)
        cl.addWidget(p)

        current_latest = self.get_latest_round()
        info = QLabel(f"현재 캐시 최신 회차: {current_latest}")
        info.setObjectName("Muted")
        cl.addWidget(info)
        self.cache_latest_label = info

        row = QHBoxLayout()
        row.setSpacing(12)

        self.latest_round_input = QLineEdit()
        self.latest_round_input.setPlaceholderText("최신 회차 입력 예: 1219")
        self.latest_round_input.setFixedHeight(42)
        row.addWidget(self.latest_round_input, 1)

        update_btn = QPushButton("최신화")
        update_btn.setObjectName("PrimaryBtn")
        update_btn.setFixedHeight(42)
        update_btn.clicked.connect(self.on_update_cache_by_input)
        row.addWidget(update_btn)

        cl.addLayout(row)

        self.update_result_label = QLabel("입력한 최신 회차까지 누락분만 가져옵니다.")
        self.update_result_label.setObjectName("Muted")
        cl.addWidget(self.update_result_label)

        layout.addWidget(card)
        layout.addStretch(1)
        return page


# ============================================================
# Main
# ============================================================
def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    w = LottoApp()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
