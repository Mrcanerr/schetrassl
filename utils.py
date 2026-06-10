from config import ROOT_ID
import database as db


async def get_role(user_id: int) -> str:
    """Return 'root', 'owner', or 'user'."""
    if user_id == ROOT_ID:
        return "root"
    if await db.is_owner(user_id):
        return "owner"
    return "user"


def parse_hours(raw: str) -> list[int] | None:
    """Parse comma-separated hours string. Returns None if invalid."""
    try:
        hours = [int(h.strip()) for h in raw.split(",") if h.strip()]
        if not hours:
            return None
        if any(h < 0 or h > 23 for h in hours):
            return None
        return hours
    except ValueError:
        return None


def hours_to_str(hours: list[int]) -> str:
    return ",".join(str(h) for h in hours)


def fmt_hours_display(hours_str: str) -> str:
    return ", ".join(f"{h}:00" for h in hours_str.split(","))
