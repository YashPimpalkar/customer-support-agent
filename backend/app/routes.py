"""FastAPI REST API Router containing all endpoints for AeroAssist."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from . import config
from .agents import AgentManager
from .db import DatabaseService
from .scripts.seed import run_migration

router = APIRouter(prefix="/api", tags=["AeroAssist API"])


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------


class ChatMessageRequest(BaseModel):
    passenger_id: str = Field(default="3442 587242", description="Passenger ID")
    message: str = Field(..., description="User query or instruction")
    thread_id: Optional[str] = Field(default=None, description="Session thread ID")
    mode: str = Field(default="part3", description="part1, part2, part3, or part4")


class ApproveActionRequest(BaseModel):
    passenger_id: str = Field(default="3442 587242", description="Passenger ID")
    thread_id: str = Field(..., description="Session thread ID")
    action_id: str = Field(..., description="Action UUID to approve or deny")
    approved: bool = Field(default=True, description="True to approve, False to deny")
    reason: Optional[str] = Field(default=None, description="Optional decline reason")
    mode: str = Field(default="part3", description="Agent architecture mode")


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------


@router.get("/health")
def health_check():
    """Health check endpoint showing database connection and AI model status."""
    try:
        stats = DatabaseService.get_database_stats()
        return {
            "status": "healthy",
            "database": "connected (Neon PostgreSQL)",
            "model": config.GOOGLE_MODEL,
            "available_modes": [
                {
                    "id": "part1",
                    "name": "Part 1: Zero-Shot",
                    "description": "Single agent, runs all tools immediately without approval",
                },
                {
                    "id": "part2",
                    "name": "Part 2: Full Confirmation",
                    "description": "Pauses before every tool call for human confirmation",
                },
                {
                    "id": "part3",
                    "name": "Part 3: Conditional Interrupt",
                    "description": "Safe tools run automatically; sensitive tools pause",
                },
                {
                    "id": "part4",
                    "name": "Part 4: Specialized Multi-Agent",
                    "description": "Primary router delegating to specialized flight, car, hotel & excursion agents",
                },
            ],
            "default_mode": "part3",
            "table_stats": stats,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "database": f"connection error: {str(exc)}", "model": config.GOOGLE_MODEL},
        )


# ---------------------------------------------------------------------------
# Passengers & Itineraries
# ---------------------------------------------------------------------------


@router.get("/passengers")
def list_passengers():
    """List passengers with upcoming flights to switch profiles in UI."""
    try:
        passengers = DatabaseService.get_passengers()
        return {"passengers": passengers}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/passengers/{passenger_id}/overview")
def passenger_overview(passenger_id: str):
    """Retrieve full itinerary and reservations for a passenger."""
    try:
        overview = DatabaseService.get_passenger_overview(passenger_id)
        return overview
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Catalog Services (Flights, Hotels, Cars, Excursions)
# ---------------------------------------------------------------------------


@router.get("/flights")
def get_flights(
    departure: Optional[str] = Query(None, description="Departure airport code"),
    arrival: Optional[str] = Query(None, description="Arrival airport code"),
    limit: int = Query(50, description="Max flights to return"),
):
    """Search scheduled flights."""
    try:
        flights = DatabaseService.get_flights(departure=departure, arrival=arrival, limit=limit)
        return {"flights": flights}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/car-rentals")
def get_car_rentals(location: Optional[str] = Query(None, description="City location")):
    """Search car rentals."""
    try:
        cars = DatabaseService.get_car_rentals(location=location)
        return {"car_rentals": cars}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/hotels")
def get_hotels(location: Optional[str] = Query(None, description="City location")):
    """Search hotels."""
    try:
        hotels = DatabaseService.get_hotels(location=location)
        return {"hotels": hotels}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/excursions")
def get_excursions(location: Optional[str] = Query(None, description="City location")):
    """Search excursions."""
    try:
        excursions = DatabaseService.get_trip_recommendations(location=location)
        return {"excursions": excursions}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/database/stats")
def database_stats():
    """Fetch live row counts across all Neon PostgreSQL tables."""
    try:
        stats = DatabaseService.get_database_stats()
        return {"stats": stats}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/database/seed")
def reseed_database():
    """Re-seed sample records into Neon PostgreSQL."""
    try:
        run_migration()
        stats = DatabaseService.get_database_stats()
        return {"message": "Database reseeded successfully", "stats": stats}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Chat & Human-In-The-Loop Approval Endpoints
# ---------------------------------------------------------------------------


@router.get("/chat/history/{session_id}")
def chat_history(session_id: str):
    """Retrieve chat message history for a given thread."""
    try:
        messages = DatabaseService.get_chat_messages(session_id)
        return {"messages": messages}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat")
def send_chat_message(req: ChatMessageRequest):
    """Process a passenger message through the LangGraph AI agent."""
    user_message = req.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    thread_id = req.thread_id or str(uuid.uuid4())

    try:
        # Save user message to PostgreSQL
        DatabaseService.save_chat_message(
            session_id=thread_id,
            role="user",
            content=user_message,
            passenger_id=req.passenger_id,
        )

        # Run through selected LangGraph architecture (part1, part2, part3, or part4)
        result = AgentManager.process_message(
            passenger_id=req.passenger_id,
            thread_id=thread_id,
            user_message=user_message,
            mode=req.mode,
        )

        # If completed, save assistant message
        if result.get("status") == "completed":
            DatabaseService.save_chat_message(
                session_id=thread_id,
                role="assistant",
                content=result.get("message", ""),
                tool_calls=[{"name": name} for name in result.get("tool_calls", [])],
                passenger_id=req.passenger_id,
            )

        return {
            **result,
            "thread_id": thread_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat/approve")
def approve_action(req: ApproveActionRequest):
    """Approve or deny a pending sensitive action in LangGraph."""
    try:
        result = AgentManager.resolve_action(
            passenger_id=req.passenger_id,
            thread_id=req.thread_id,
            action_id=req.action_id,
            approved=req.approved,
            reason=req.reason,
            mode=req.mode,
        )

        # Save resulting assistant message
        if result.get("status") == "completed":
            DatabaseService.save_chat_message(
                session_id=req.thread_id,
                role="assistant",
                content=result.get("message", ""),
                tool_calls=[{"name": name} for name in result.get("tool_calls", [])],
                passenger_id=req.passenger_id,
            )

        return {
            **result,
            "thread_id": req.thread_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
