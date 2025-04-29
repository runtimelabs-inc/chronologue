from fastapi import FastAPI
from api import orders
from api import approval
from api import feedback

app = FastAPI(
    title="Chronologue Memory Orchestration API",
    description="API for managing recurring grocery orders, approvals, deliveries, and calendar integration.",
    version="0.1.0"
)

# Register routers
app.include_router(orders.router, prefix="/api")
app.include_router(approval.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
