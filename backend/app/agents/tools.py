"""LangChain tools connected to the Neon PostgreSQL database.

Includes Safe Tools (automatic read-only queries) and Sensitive Tools
(human-in-the-loop approval required before mutating data).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from psycopg2.extras import RealDictCursor

from ..db import get_db
from ..rag import get_retriever


def _passenger_id(cfg: RunnableConfig) -> str:
    passenger_id = cfg.get("configurable", {}).get("passenger_id")
    if not passenger_id:
        raise ValueError("No passenger_id configured for this session.")
    return passenger_id


# ---------------------------------------------------------------------------
# Policy lookup (RAG)
# ---------------------------------------------------------------------------


@tool
def lookup_policy(query: str) -> str:
    """Look up the airline company policies to answer questions about ticket changes,
    cancellations, baggage limits, car rentals, hotels, excursions, special assistance,
    or pet travel. Always consult this before telling a customer whether an action is allowed.
    """
    hits = get_retriever().query(query, k=2)
    return "\n\n".join(h.text for h in hits)


# ---------------------------------------------------------------------------
# Flights Tools
# ---------------------------------------------------------------------------


@tool
def fetch_user_flight_information(config: RunnableConfig) -> List[Dict[str, Any]]:
    """Fetch all tickets, flights, and seat assignments for the currently signed-in passenger.
    Call this first, before answering any question about 'my' flights or tickets,
    and before booking/changing anything.
    """
    passenger_id = _passenger_id(config)
    sql = """
        SELECT
            t.ticket_no, t.book_ref, t.passenger_id, t.passenger_name,
            f.flight_id, f.flight_no, f.departure_airport, f.arrival_airport,
            f.scheduled_departure, f.scheduled_arrival, f.status,
            bp.seat_no, tf.fare_conditions, tf.amount
        FROM tickets t
        JOIN ticket_flights tf ON t.ticket_no = tf.ticket_no
        JOIN flights f ON tf.flight_id = f.flight_id
        LEFT JOIN boarding_passes bp
            ON bp.ticket_no = t.ticket_no AND bp.flight_id = f.flight_id
        WHERE t.passenger_id = %s
        ORDER BY f.scheduled_departure
    """
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (passenger_id,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


@tool
def search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search for scheduled flights in PostgreSQL, optionally filtered by departure/arrival airport
    (IATA code, e.g. 'JFK', 'BSL', 'CDG') and scheduled departure window.
    """
    sql = "SELECT * FROM flights WHERE 1 = 1"
    params: list = []
    if departure_airport:
        sql += " AND departure_airport = %s"
        params.append(departure_airport.upper())
    if arrival_airport:
        sql += " AND arrival_airport = %s"
        params.append(arrival_airport.upper())
    if start_time:
        sql += " AND scheduled_departure >= %s"
        params.append(start_time)
    if end_time:
        sql += " AND scheduled_departure <= %s"
        params.append(end_time)
    sql += " ORDER BY scheduled_departure LIMIT %s"
    params.append(limit)

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


@tool
def update_ticket_to_new_flight(ticket_no: str, new_flight_id: int, config: RunnableConfig) -> str:
    """Re-book an existing flight ticket onto a different flight. Only allowed on tickets
    belonging to the current passenger, and only if the new flight's scheduled departure
    is at least 3 hours away.
    """
    passenger_id = _passenger_id(config)
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM flights WHERE flight_id = %s", (new_flight_id,))
            new_flight = cur.fetchone()
            if not new_flight:
                return f"No flight found with flight_id={new_flight_id}."

            departure = pd.to_datetime(new_flight["scheduled_departure"])
            now = pd.Timestamp.now(tz=departure.tz) if departure.tzinfo else pd.Timestamp.now()
            if (departure - now).total_seconds() < 3 * 3600:
                return (
                    f"Cannot rebook onto flight {new_flight_id}: departure at "
                    f"{departure} is less than 3 hours from now."
                )

            cur.execute(
                "SELECT * FROM tickets WHERE ticket_no = %s AND passenger_id = %s",
                (ticket_no, passenger_id),
            )
            owns_ticket = cur.fetchone()
            if not owns_ticket:
                return f"Ticket {ticket_no} does not belong to passenger {passenger_id}."

            cur.execute(
                "UPDATE ticket_flights SET flight_id = %s WHERE ticket_no = %s",
                (new_flight_id, ticket_no),
            )
            conn.commit()
            return f"Ticket {ticket_no} successfully re-booked onto flight {new_flight_id} ({new_flight.get('flight_no')})."


@tool
def cancel_ticket(ticket_no: str, config: RunnableConfig) -> str:
    """Cancel a flight ticket. Only allowed on tickets belonging to the current passenger."""
    passenger_id = _passenger_id(config)
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM tickets WHERE ticket_no = %s AND passenger_id = %s",
                (ticket_no, passenger_id),
            )
            owns_ticket = cur.fetchone()
            if not owns_ticket:
                return f"Ticket {ticket_no} does not belong to passenger {passenger_id}."

            cur.execute("DELETE FROM ticket_flights WHERE ticket_no = %s", (ticket_no,))
            conn.commit()
            return f"Ticket {ticket_no} has been successfully cancelled."


# ---------------------------------------------------------------------------
# Car Rental Tools
# ---------------------------------------------------------------------------


@tool
def search_car_rentals(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for available rental cars in PostgreSQL by city/location, company name, or price tier."""
    sql = "SELECT * FROM car_rentals WHERE 1=1"
    params: list = []
    if location:
        sql += " AND location ILIKE %s"
        params.append(f"%{location}%")
    if name:
        sql += " AND name ILIKE %s"
        params.append(f"%{name}%")
    if price_tier:
        sql += " AND price_tier ILIKE %s"
        params.append(price_tier)

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


@tool
def book_car_rental(rental_id: int, config: RunnableConfig) -> str:
    """Book the car rental with the specified ID for the passenger."""
    passenger_id = _passenger_id(config)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE car_rentals SET booked = 1, passenger_id = %s WHERE id = %s",
                (passenger_id, rental_id),
            )
            conn.commit()
            if cur.rowcount:
                return f"Car rental #{rental_id} successfully booked for passenger {passenger_id}."
            return f"No car rental found with id={rental_id}."


@tool
def update_car_rental(
    rental_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """Update pickup or return dates of a booked car rental."""
    with get_db() as conn:
        with conn.cursor() as cur:
            if start_date:
                cur.execute("UPDATE car_rentals SET start_date = %s WHERE id = %s", (str(start_date), rental_id))
            if end_date:
                cur.execute("UPDATE car_rentals SET end_date = %s WHERE id = %s", (str(end_date), rental_id))
            conn.commit()
            return f"Car rental #{rental_id} booking dates updated."


@tool
def cancel_car_rental(rental_id: int) -> str:
    """Cancel a booked car rental reservation."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE car_rentals SET booked = 0, passenger_id = NULL WHERE id = %s", (rental_id,))
            conn.commit()
            if cur.rowcount:
                return f"Car rental #{rental_id} has been cancelled."
            return f"No car rental found with id={rental_id}."


# ---------------------------------------------------------------------------
# Hotel Tools
# ---------------------------------------------------------------------------


@tool
def search_hotels(
    location: Optional[str] = None,
    name: Optional[str] = None,
    price_tier: Optional[str] = None,
    checkin_date: Optional[str] = None,
    checkout_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for available hotel rooms in PostgreSQL filtered by city, hotel brand, or tier."""
    sql = "SELECT * FROM hotels WHERE 1=1"
    params: list = []
    if location:
        sql += " AND location ILIKE %s"
        params.append(f"%{location}%")
    if name:
        sql += " AND name ILIKE %s"
        params.append(f"%{name}%")
    if price_tier:
        sql += " AND price_tier ILIKE %s"
        params.append(price_tier)

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


@tool
def book_hotel(hotel_id: int, config: RunnableConfig) -> str:
    """Reserve the hotel room with the specified ID."""
    passenger_id = _passenger_id(config)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE hotels SET booked = 1, passenger_id = %s WHERE id = %s",
                (passenger_id, hotel_id),
            )
            conn.commit()
            if cur.rowcount:
                return f"Hotel reservation #{hotel_id} confirmed for passenger {passenger_id}."
            return f"No hotel found with id={hotel_id}."


@tool
def update_hotel(
    hotel_id: int,
    checkin_date: Optional[str] = None,
    checkout_date: Optional[str] = None,
) -> str:
    """Update check-in and check-out dates for a booked hotel reservation."""
    with get_db() as conn:
        with conn.cursor() as cur:
            if checkin_date:
                cur.execute("UPDATE hotels SET checkin_date = %s WHERE id = %s", (str(checkin_date), hotel_id))
            if checkout_date:
                cur.execute("UPDATE hotels SET checkout_date = %s WHERE id = %s", (str(checkout_date), hotel_id))
            conn.commit()
            return f"Hotel reservation #{hotel_id} stay dates updated."


@tool
def cancel_hotel(hotel_id: int) -> str:
    """Cancel a booked hotel reservation."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE hotels SET booked = 0, passenger_id = NULL WHERE id = %s", (hotel_id,))
            conn.commit()
            if cur.rowcount:
                return f"Hotel reservation #{hotel_id} has been cancelled."
            return f"No hotel found with id={hotel_id}."


# ---------------------------------------------------------------------------
# Excursions / Trip Recommendations Tools
# ---------------------------------------------------------------------------


@tool
def search_trip_recommendations(
    location: Optional[str] = None,
    name: Optional[str] = None,
    keywords: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for activities, landmarks, and excursions in PostgreSQL."""
    sql = "SELECT * FROM trip_recommendations WHERE 1=1"
    params: list = []
    if location:
        sql += " AND location ILIKE %s"
        params.append(f"%{location}%")
    if name:
        sql += " AND name ILIKE %s"
        params.append(f"%{name}%")
    if keywords:
        for kw in [k.strip() for k in keywords.split(",") if k.strip()]:
            sql += " AND keywords ILIKE %s"
            params.append(f"%{kw}%")

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [dict(r) for r in rows]


@tool
def book_excursion(recommendation_id: int, config: RunnableConfig) -> str:
    """Book the excursion or activity with the specified ID."""
    passenger_id = _passenger_id(config)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE trip_recommendations SET booked = 1, passenger_id = %s WHERE id = %s",
                (passenger_id, recommendation_id),
            )
            conn.commit()
            if cur.rowcount:
                return f"Excursion #{recommendation_id} booked successfully for passenger {passenger_id}."
            return f"No excursion found with id={recommendation_id}."


@tool
def update_excursion(recommendation_id: int, details: str) -> str:
    """Update notes or details on a booked excursion."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE trip_recommendations SET details = %s WHERE id = %s",
                (details, recommendation_id),
            )
            conn.commit()
            if cur.rowcount:
                return f"Excursion #{recommendation_id} details updated."
            return f"No excursion found with id={recommendation_id}."


@tool
def cancel_excursion(recommendation_id: int) -> str:
    """Cancel a booked excursion activity."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE trip_recommendations SET booked = 0, passenger_id = NULL WHERE id = %s",
                (recommendation_id,),
            )
            conn.commit()
            if cur.rowcount:
                return f"Excursion #{recommendation_id} cancelled."
            return f"No excursion found with id={recommendation_id}."


# ---------------------------------------------------------------------------
# Tool Classifications
# ---------------------------------------------------------------------------

SAFE_TOOLS = [
    lookup_policy,
    fetch_user_flight_information,
    search_flights,
    search_car_rentals,
    search_hotels,
    search_trip_recommendations,
]

SENSITIVE_TOOLS = [
    update_ticket_to_new_flight,
    cancel_ticket,
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
    book_hotel,
    update_hotel,
    cancel_hotel,
    book_excursion,
    update_excursion,
    cancel_excursion,
]

ALL_TOOLS = SAFE_TOOLS + SENSITIVE_TOOLS

FLIGHT_SAFE_TOOLS = [search_flights]
FLIGHT_SENSITIVE_TOOLS = [update_ticket_to_new_flight, cancel_ticket]

CAR_RENTAL_SAFE_TOOLS = [search_car_rentals]
CAR_RENTAL_SENSITIVE_TOOLS = [book_car_rental, update_car_rental, cancel_car_rental]

HOTEL_SAFE_TOOLS = [search_hotels]
HOTEL_SENSITIVE_TOOLS = [book_hotel, update_hotel, cancel_hotel]

EXCURSION_SAFE_TOOLS = [search_trip_recommendations]
EXCURSION_SENSITIVE_TOOLS = [book_excursion, update_excursion, cancel_excursion]

PRIMARY_ASSISTANT_TOOLS = [lookup_policy, fetch_user_flight_information]
