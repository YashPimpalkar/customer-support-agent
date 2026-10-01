"""Routing and delegation schemas for Part 4 specialized multi-agent workflows."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToFlightBookingAssistant(BaseModel):
    """Transfer the conversation to a specialized assistant that handles flight ticket changes and cancellations."""

    request: str = Field(
        description="Any followup question(s) the flight assistant should clarify with the user, or a summary of what the user wants."
    )


class ToBookCarRental(BaseModel):
    """Transfer the conversation to a specialized assistant that handles car rental searches and bookings."""

    location: str = Field(description="City or area the user wants a rental car in.")
    start_date: str = Field(default="", description="Rental start date.")
    end_date: str = Field(default="", description="Rental end date.")
    request: str = Field(description="Any additional detail about what the user wants.")


class ToHotelBookingAssistant(BaseModel):
    """Transfer the conversation to a specialized assistant that handles hotel searches and bookings."""

    location: str = Field(description="City the user wants a hotel in.")
    checkin_date: str = Field(default="", description="Check-in date.")
    checkout_date: str = Field(default="", description="Check-out date.")
    request: str = Field(description="Any additional detail about what the user wants.")


class ToBookExcursion(BaseModel):
    """Transfer the conversation to a specialized assistant that handles trip recommendations and excursion bookings."""

    location: str = Field(description="City the user wants activity recommendations for.")
    request: str = Field(description="Any additional detail about what the user wants.")


class CompleteOrEscalate(BaseModel):
    """Called by a specialized assistant to mark its task done, or to hand control back to the primary assistant."""

    cancel: bool = True
    reason: str
