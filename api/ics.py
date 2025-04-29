from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from datetime import datetime, timedelta
from api.orders import order_memory_db

router = APIRouter()

# ------------------------------
# Helper Functions
# ------------------------------

def build_ics_event(summary: str, description: str, start_time: datetime, end_time: datetime, recurrence: str = None) -> str:
    event = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Chronologue//EN",
        "BEGIN:VEVENT",
        f"UID:{datetime.utcnow().timestamp()}@chronologue.ai",
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{start_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{end_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
    ]
    if recurrence:
        event.append(f"RRULE:{recurrence}")
    event.append("STATUS:CONFIRMED")
    event.append("END:VEVENT")
    event.append("END:VCALENDAR")
    return "\r\n".join(event)

# ------------------------------
# Endpoints
# ------------------------------

@router.get("/ics/{order_id}/purchase")
async def generate_purchase_ics(order_id: str):
    order = order_memory_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Set times
    now = datetime.utcnow()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=30)

    recurrence = "FREQ=WEEKLY;INTERVAL=1"
    description = "Approve your grocery order.\nVisit: https://chronologue.ai/weekly-orders/" + order_id

    ics_content = build_ics_event(
        summary="Grocery Order Approval",
        description=description,
        start_time=start_time,
        end_time=end_time,
        recurrence=recurrence
    )

    return Response(content=ics_content, media_type="text/calendar")

@router.get("/ics/{order_id}/delivery")
async def generate_delivery_ics(order_id: str):
    order = order_memory_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    now = datetime.utcnow()
    start_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)

    recurrence = "FREQ=WEEKLY;INTERVAL=1"
    description = "Grocery delivery scheduled.\nFeedback: https://chronologue.ai/feedback/" + order_id

    ics_content = build_ics_event(
        summary="Grocery Delivery Scheduled",
        description=description,
        start_time=start_time,
        end_time=end_time,
        recurrence=recurrence
    )

    return Response(content=ics_content, media_type="text/calendar")
