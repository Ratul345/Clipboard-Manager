"""Design tokens and shared styling for the Clipboard Manager UI.

Every window pulls its colours from a Theme so light and dark mode stay
consistent. build_stylesheet() produces the Qt style sheet shared by the main
window and the settings window.
"""

from dataclasses import dataclass
from typing import Optional

from PyQt5.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QPalette


@dataclass(frozen=True)
class Theme:
    name: str
    is_dark: bool
    bg: str              # window panel
    surface: str         # cards and inputs
    surface_hover: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_soft: str     # selected card / checked chip background
    on_accent: str
    danger: str
    danger_soft: str
    highlight_bg: str    # search match background
    highlight_fg: str
    type_text: str
    type_link: str
    type_image: str
    shadow_alpha: int


LIGHT = Theme(
    name='light', is_dark=False,
    bg='#F5F6F8', surface='#FFFFFF', surface_hover='#F0F2F5',
    border='#E3E6EB', border_strong='#CBD0D8',
    text='#161A22', text_muted='#6B7280',
    accent='#2B7FD8', accent_hover='#1F6BBD', accent_soft='#E8F2FD', on_accent='#FFFFFF',
    danger='#D92D20', danger_soft='#FEECEA',
    highlight_bg='#FFE58A', highlight_fg='#4A3B00',
    type_text='#2B7FD8', type_link='#0E9F8E', type_image='#D9822B',
    shadow_alpha=110,
)

DARK = Theme(
    name='dark', is_dark=True,
    bg='#17191E', surface='#21242B', surface_hover='#292D35',
    border='#2F343D', border_strong='#444B57',
    text='#F1F3F6', text_muted='#9AA3B2',
    accent='#4C9BF0', accent_hover='#6AAEF5', accent_soft='#1D2E44', on_accent='#0B1320',
    danger='#F97066', danger_soft='#3B2220',
    highlight_bg='#6B5A12', highlight_fg='#FFF1B8',
    type_text='#4C9BF0', type_link='#2FC4B0', type_image='#F0A04C',
    shadow_alpha=200,
)

THEME_CHOICES = ('light', 'dark', 'system')

_FONT_CANDIDATES = ['Segoe UI', 'Inter', 'Ubuntu', 'Noto Sans', 'Cantarell', 'DejaVu Sans']
_font_family_cache: Optional[str] = None


def system_prefers_dark() -> bool:
    """Best-effort detection of a dark OS theme from the Qt palette."""
    try:
        return QGuiApplication.palette().color(QPalette.Window).lightness() < 128
    except Exception:
        return False


def resolve_theme(name: Optional[str]) -> Theme:
    """Map a config value ('light', 'dark', 'system') to a Theme."""
    if name == 'dark':
        return DARK
    if name == 'system':
        return DARK if system_prefers_dark() else LIGHT
    return LIGHT


def font_family() -> str:
    """First installed family from the preferred UI font list."""
    global _font_family_cache
    if _font_family_cache is None:
        installed = set(QFontDatabase().families())
        _font_family_cache = next(
            (f for f in _FONT_CANDIDATES if f in installed),
            QFont().family()
        )
    return _font_family_cache


def ui_font(pixel_size: int = 13, weight: int = QFont.Normal) -> QFont:
    """A UI font with a pixel size, so text scales the same on every platform."""
    font = QFont(font_family())
    font.setPixelSize(pixel_size)
    font.setWeight(weight)
    return font


def type_color(theme: Theme, content_type: str) -> str:
    return {
        'link': theme.type_link,
        'image': theme.type_image,
    }.get(content_type, theme.type_text)


def with_alpha(color: str, alpha: int) -> QColor:
    c = QColor(color)
    c.setAlpha(alpha)
    return c


def build_stylesheet(t: Theme) -> str:
    """Qt style sheet shared by the main and settings windows."""
    family = ", ".join(f"'{f}'" for f in _FONT_CANDIDATES) + ", sans-serif"
    return f"""
    QWidget {{
        font-family: {family};
        font-size: 13px;
        color: {t.text};
    }}
    QLabel {{ background: transparent; }}
    QLabel[role="title"] {{ font-size: 15px; font-weight: 600; }}
    QLabel[role="rowtitle"] {{ font-size: 13px; font-weight: 600; }}
    QLabel[role="muted"] {{ color: {t.text_muted}; font-size: 12px; }}
    QLabel[role="hint"] {{ color: {t.text_muted}; font-size: 11px; }}

    QToolTip {{
        background-color: {t.surface}; color: {t.text};
        border: 1px solid {t.border}; padding: 4px 8px; border-radius: 6px;
    }}
    QMessageBox, QDialog {{ background-color: {t.bg}; }}
    QMessageBox QLabel {{ color: {t.text}; }}

    QLineEdit {{
        background: {t.surface}; border: 1px solid {t.border}; border-radius: 10px;
        padding: 0 12px; min-height: 38px;
        selection-background-color: {t.accent}; selection-color: {t.on_accent};
    }}
    QLineEdit:hover {{ border-color: {t.border_strong}; }}
    QLineEdit:focus {{ border: 1px solid {t.accent}; }}
    QLineEdit:read-only {{ background: {t.surface_hover}; }}

    QSpinBox {{
        background: {t.surface}; border: 1px solid {t.border}; border-radius: 8px;
        padding: 0 10px; min-height: 34px; min-width: 110px;
        selection-background-color: {t.accent}; selection-color: {t.on_accent};
    }}
    QSpinBox:hover {{ border-color: {t.border_strong}; }}
    QSpinBox:focus {{ border: 1px solid {t.accent}; }}

    QPushButton {{
        background: {t.surface}; border: 1px solid {t.border}; border-radius: 8px;
        padding: 0 16px; min-height: 34px; min-width: 64px; font-weight: 600;
    }}
    QPushButton:hover {{ background: {t.surface_hover}; border-color: {t.border_strong}; }}
    QPushButton:disabled {{ color: {t.text_muted}; }}

    QPushButton[variant="primary"] {{
        background: {t.accent}; color: {t.on_accent}; border: 1px solid {t.accent};
    }}
    QPushButton[variant="primary"]:hover {{ background: {t.accent_hover}; border-color: {t.accent_hover}; }}

    QPushButton[variant="danger"] {{ color: {t.danger}; }}
    QPushButton[variant="danger"]:hover {{ background: {t.danger_soft}; border-color: {t.danger}; }}

    QPushButton[variant="ghost"], QPushButton[variant="ghost-danger"] {{
        background: transparent; border: none; border-radius: 6px;
        color: {t.text_muted}; padding: 0 10px; min-height: 28px; min-width: 0px;
        font-weight: 500; font-size: 12px;
    }}
    QPushButton[variant="ghost"]:hover {{ background: {t.surface_hover}; color: {t.text}; }}
    QPushButton[variant="ghost-danger"]:hover {{ background: {t.danger_soft}; color: {t.danger}; }}

    QPushButton[variant="icon"], QPushButton[variant="icon-danger"] {{
        background: transparent; border: none; border-radius: 8px;
        padding: 0; min-height: 0px; min-width: 0px;
    }}
    QPushButton[variant="icon"]:hover {{ background: {t.surface_hover}; }}
    QPushButton[variant="icon-danger"]:hover {{ background: {t.danger_soft}; }}

    QPushButton[chip="true"] {{
        background: transparent; border: 1px solid {t.border}; border-radius: 14px;
        padding: 0 13px; min-height: 26px; min-width: 0px;
        color: {t.text_muted}; font-size: 12px; font-weight: 500;
    }}
    QPushButton[chip="true"]:hover {{ background: {t.surface_hover}; color: {t.text}; }}
    QPushButton[chip="true"]:checked {{
        background: {t.accent_soft}; border: 1px solid {t.accent};
        color: {t.accent}; font-weight: 600;
    }}

    QListWidget {{ background: transparent; border: none; outline: none; }}
    QScrollArea {{ background: transparent; border: none; }}

    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px 0; }}
    QScrollBar::handle:vertical {{
        background: {t.border_strong}; border-radius: 4px; min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {t.text_muted}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
    """
