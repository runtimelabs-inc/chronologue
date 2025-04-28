from datetime import datetime, timedelta
from pathlib import Path
import json
from ics import Calendar, Event

def load_orders_from_json(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def format_order_description(order_list: list) -> str:
    """
    Create a readable description for the calendar event from the order list.
    """
    lines = []
    for item in order_list:
        line = f"{item['quantity']} x {item['item']} ({item['link']})"
        lines.append(line)
    return "\n".join(lines)

def generate_order_event(
    order_type: str,
    order_items: list,
    event_time: datetime,
    recurrence: str = None  # e.g., "WEEKLY" or "MONTHLY"
) -> Event:
    event = Event()
    event.name = f"Grocery Order - {order_type.capitalize()}"
    event.begin = event_time
    event.duration = timedelta(minutes=30)
    event.description = format_order_description(order_items)

    if recurrence:
        # RRULE for weekly or monthly recurrence
        event.extra.append(("RRULE", f"FREQ={recurrence};INTERVAL=1"))

    return event

def create_order_calendar(orders: dict, start_date: datetime) -> Calendar:
    calendar = Calendar()

    # Weekly Orders
    if orders.get("weekly"):
        weekly_event = generate_order_event(
            order_type="weekly",
            order_items=orders["weekly"],
            event_time=start_date.replace(hour=8, minute=0),
            recurrence="WEEKLY"
        )
        calendar.events.add(weekly_event)

    # Monthly Orders
    if orders.get("monthly"):
        monthly_event = generate_order_event(
            order_type="monthly",
            order_items=orders["monthly"],
            event_time=start_date.replace(day=1, hour=8, minute=0),
            recurrence="MONTHLY"
        )
        calendar.events.add(monthly_event)

    return calendar

def save_calendar_to_ics(calendar: Calendar, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(calendar.serialize_iter())

if __name__ == "__main__":
    # Example usage
    input_json = "grocery_orders.json"
    output_ics = "grocery_schedule.ics"

    orders = load_orders_from_json(input_json)
    today = datetime.utcnow()

    calendar = create_order_calendar(orders, start_date=today)
    save_calendar_to_ics(calendar, output_ics)

    print(f"ICS calendar created: {output_ics}")
