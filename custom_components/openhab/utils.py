"""Utils"""


def strip_ip(url: str):
    """Strip IP/Hostname from URL"""
    return url.split("/")[2].split(":")[0]


def sanitize_entity_id(text: str) -> str:
    """Sanitize text for use in entity IDs (lowercase, replace dots/invalid chars with underscores)."""
    return text.lower().replace(".", "_").replace("-", "_").replace(" ", "_")


def str_to_hsv(state: str) -> tuple[float, float, float]:
    """Convert state string to hsv tuple"""
    color = state.split(",")
    return [float(color[0]), float(color[1]), float(color[2])]


def hsv_to_str(hsv: tuple[float, float, float]) -> str:
    """Convert state string to hsv tuple"""
    return f"{round(hsv[0])},{round(hsv[1])},{round(hsv[2])}"
