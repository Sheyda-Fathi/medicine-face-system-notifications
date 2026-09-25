"""Pure helpers for medication times and dose status."""

from datetime import date, datetime


def parse_time_slots(raw_value):
    slots = []
    for value in (raw_value or "").split(","):
        value = value.strip()
        if not value:
            continue
        try:
            normalized = datetime.strptime(value, "%H:%M").strftime("%H:%M")
        except ValueError:
            continue
        if normalized not in slots:
            slots.append(normalized)
    return sorted(slots)


def dose_status(slot, taken=None, now=None, target_date=None):
    if taken is True:
        return "Taken"
    if taken is False:
        return "Missed"

    now = now or datetime.now()
    target_date = target_date or date.today()
    scheduled_at = datetime.combine(
        target_date,
        datetime.strptime(slot, "%H:%M").time(),
    )
    return "Missed" if scheduled_at < now else "Pending"


def format_recorded_at(value):
    if not value:
        return "-"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)
