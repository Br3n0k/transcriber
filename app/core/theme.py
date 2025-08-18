from typing import TypedDict


class ThemeColors(TypedDict):
    primary: str
    secondary: str
    accent: str


def default_theme() -> ThemeColors:
    return {
        "primary": "#6366F1",  # indigo-500
        "secondary": "#10B981",  # emerald-500
        "accent": "#F59E0B",  # amber-500
    }