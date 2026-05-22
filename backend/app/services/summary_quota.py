"""Per-user daily AI summary quota tied to parse task_ids."""

from datetime import date

from app.core.config import settings

# user_id (str) -> {"date": "YYYY-MM-DD", "task_ids": [str, ...]}
_daily_usage: dict[str, dict] = {}


def _today() -> str:
    return date.today().isoformat()


def _entry_for_user(user_id: str) -> dict:
    uid = str(user_id)
    entry = _daily_usage.get(uid)
    if not entry or entry.get("date") != _today():
        entry = {"date": _today(), "task_ids": []}
        _daily_usage[uid] = entry
    return entry


def free_summarize_slots_used(user_id: str) -> int:
    return len(_entry_for_user(user_id)["task_ids"])


def can_start_summarize(user_id: str, task_id: str, *, is_pro: bool) -> tuple[bool, str | None]:
    if is_pro:
        return True, None
    entry = _entry_for_user(user_id)
    if task_id in entry["task_ids"]:
        return True, None
    limit = settings.FREE_DAILY_SUMMARIZE_LIMIT
    if len(entry["task_ids"]) >= limit:
        return (
            False,
            f"Daily free summary limit reached ({limit} videos per day). Upgrade to PRO for unlimited summaries.",
        )
    return True, None


def record_summarize_task(user_id: str, task_id: str, *, is_pro: bool) -> None:
    if is_pro:
        return
    entry = _entry_for_user(user_id)
    if task_id not in entry["task_ids"]:
        entry["task_ids"].append(task_id)
