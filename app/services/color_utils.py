"""
Color utilities for brand-consistent image generation.
Converts hex codes to Imagen-friendly color descriptions.
"""

import colorsys
from typing import Dict, Tuple


# Named colors for common hex values (exact matches)
NAMED_COLORS: Dict[str, str] = {
    "#ffffff": "white",
    "#000000": "black",
    "#ff0000": "red",
    "#00ff00": "lime green",
    "#0000ff": "blue",
    "#ffff00": "yellow",
    "#00ffff": "cyan",
    "#ff00ff": "magenta",
    "#c0c0c0": "silver",
    "#808080": "gray",
    "#800000": "maroon",
    "#808000": "olive",
    "#008000": "green",
    "#800080": "purple",
    "#008080": "teal",
    "#000080": "navy",
}


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert hex code to RGB tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join([c * 2 for c in hex_code])
    return tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB to HSL (hue 0-360, saturation 0-100, lightness 0-100)."""
    r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
    h, lightness, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
    return h * 360, s * 100, lightness * 100


def get_hue_name(hue: float) -> str:
    """Get color name from hue angle (0-360)."""
    if hue < 15 or hue >= 345:
        return "red"
    elif hue < 45:
        return "orange"
    elif hue < 70:
        return "yellow"
    elif hue < 85:
        return "chartreuse"
    elif hue < 150:
        return "green"
    elif hue < 175:
        return "cyan"
    elif hue < 200:
        return "turquoise"
    elif hue < 260:
        return "blue"
    elif hue < 290:
        return "purple"
    elif hue < 330:
        return "magenta"
    else:
        return "pink"


def get_lightness_modifier(lightness: float) -> str:
    """Get lightness modifier based on HSL lightness."""
    if lightness < 20:
        return "very dark"
    elif lightness < 35:
        return "dark"
    elif lightness < 65:
        return ""  # Normal
    elif lightness < 80:
        return "light"
    else:
        return "very light"


def get_saturation_modifier(saturation: float) -> str:
    """Get saturation modifier based on HSL saturation."""
    if saturation < 10:
        return "grayish"
    elif saturation < 30:
        return "muted"
    elif saturation < 70:
        return ""  # Normal
    elif saturation < 90:
        return "vibrant"
    else:
        return "bright"


def hex_to_color_name(hex_code: str) -> str:
    """
    Convert hex code to Imagen-friendly color description.

    Examples:
        #f0fb29 -> "bright chartreuse yellow"
        #5cf0e4 -> "bright turquoise cyan"
        #1a1a1a -> "very dark gray"
        #ff5733 -> "vibrant orange red"

    Args:
        hex_code: Hex color code (with or without #)

    Returns:
        Natural language color description
    """
    hex_code = hex_code.lower().strip()
    if not hex_code.startswith("#"):
        hex_code = "#" + hex_code

    # Check for exact named color match
    if hex_code in NAMED_COLORS:
        return NAMED_COLORS[hex_code]

    # Convert to RGB and HSL
    try:
        r, g, b = hex_to_rgb(hex_code)
    except (ValueError, IndexError):
        return "neutral"

    h, s, lum = rgb_to_hsl(r, g, b)

    # Handle achromatic colors (low saturation)
    if s < 10:
        if lum < 15:
            return "black"
        elif lum < 30:
            return "very dark gray"
        elif lum < 45:
            return "dark gray"
        elif lum < 60:
            return "gray"
        elif lum < 75:
            return "light gray"
        elif lum < 90:
            return "very light gray"
        else:
            return "white"

    # Build color description
    parts = []

    # Add saturation modifier
    sat_mod = get_saturation_modifier(s)
    if sat_mod:
        parts.append(sat_mod)

    # Add lightness modifier
    light_mod = get_lightness_modifier(lum)
    if light_mod:
        parts.append(light_mod)

    # Get base hue name
    hue_name = get_hue_name(h)

    # Add secondary hue for in-between colors
    if 30 < h < 50:  # Orange-yellow
        parts.append("orange")
        parts.append("yellow")
    elif 65 < h < 85:  # Yellow-green
        parts.append("chartreuse")
        parts.append("yellow")
    elif 165 < h < 195:  # Cyan-turquoise
        parts.append("turquoise")
        parts.append("cyan")
    elif 275 < h < 310:  # Purple-magenta
        parts.append("purple")
        parts.append("magenta")
    else:
        parts.append(hue_name)

    return " ".join(parts)


def get_color_palette_description(colors: list) -> str:
    """
    Generate a natural language description of a color palette.

    Args:
        colors: List of hex color codes

    Returns:
        Description like "bright yellow and turquoise cyan with dark accents"
    """
    if not colors:
        return "neutral tones"

    descriptions = [hex_to_color_name(c) for c in colors[:3]]

    if len(descriptions) == 1:
        return descriptions[0]
    elif len(descriptions) == 2:
        return f"{descriptions[0]} and {descriptions[1]}"
    else:
        return f"{descriptions[0]}, {descriptions[1]}, and {descriptions[2]}"


def validate_hex_color(hex_code: str) -> bool:
    """Validate if a string is a valid hex color code."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) not in (3, 6):
        return False
    try:
        int(hex_code, 16)
        return True
    except ValueError:
        return False


def ensure_hex_format(color: str) -> str:
    """Ensure color string has # prefix."""
    color = color.strip()
    if not color.startswith("#"):
        return "#" + color
    return color
