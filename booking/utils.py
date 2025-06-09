from datetime import datetime, timedelta


def get_time_slots(place, date):
    slot_minutes = place.slot_duration
    current = datetime.combine(date, place.open_time)
    end = datetime.combine(date, place.close_time)
    delta = timedelta(minutes=slot_minutes)

    slots = []
    while current + delta <= end:
        slots.append((current.time(), (current + delta).time()))
        current += delta

    return slots
