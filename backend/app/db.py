"""PostgreSQL Database connection and data access layer."""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from . import config


@contextmanager
def get_db():
    """Context manager yielding a PostgreSQL database connection with RealDictCursor."""
    conn = psycopg2.connect(config.DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def query_all(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return all rows as dicts."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            return [dict(r) for r in rows]


def query_one(sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    """Execute a SELECT query and return a single row as dict."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return dict(row) if row else None


def execute_mutation(sql: str, params: Optional[tuple] = None) -> int:
    """Execute an INSERT, UPDATE, or DELETE query and return the affected row count."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.rowcount


class DatabaseService:
    """Service encapsulating database queries for the customer support application."""

    @staticmethod
    def get_passengers() -> List[Dict[str, Any]]:
        """List distinct passengers with ticket numbers and names."""
        sql = """
            SELECT DISTINCT t.passenger_id, t.passenger_name, t.ticket_no,
                   f.flight_no, f.departure_airport, f.arrival_airport,
                   f.scheduled_departure, f.status
            FROM tickets t
            LEFT JOIN ticket_flights tf ON t.ticket_no = tf.ticket_no
            LEFT JOIN flights f ON tf.flight_id = f.flight_id
            ORDER BY t.passenger_name NULLS LAST, t.passenger_id
        """
        return query_all(sql)

    @staticmethod
    def get_passenger_overview(passenger_id: str) -> Dict[str, Any]:
        """Get complete itinerary and bookings for a specific passenger."""
        tickets_sql = """
            SELECT t.ticket_no, t.book_ref, t.passenger_id, t.passenger_name,
                   f.flight_id, f.flight_no, f.departure_airport, f.arrival_airport,
                   f.scheduled_departure, f.scheduled_arrival, f.status,
                   bp.seat_no, bp.boarding_no, tf.fare_conditions, tf.amount
            FROM tickets t
            JOIN ticket_flights tf ON t.ticket_no = tf.ticket_no
            JOIN flights f ON tf.flight_id = f.flight_id
            LEFT JOIN boarding_passes bp ON bp.ticket_no = t.ticket_no AND bp.flight_id = f.flight_id
            WHERE t.passenger_id = %s
            ORDER BY f.scheduled_departure
        """
        tickets = query_all(tickets_sql, (passenger_id,))

        cars_sql = """
            SELECT * FROM car_rentals
            WHERE booked = 1 AND (passenger_id = %s OR passenger_id IS NULL)
        """
        cars = query_all(cars_sql, (passenger_id,))

        hotels_sql = """
            SELECT * FROM hotels
            WHERE booked = 1 AND (passenger_id = %s OR passenger_id IS NULL)
        """
        hotels = query_all(hotels_sql, (passenger_id,))

        excursions_sql = """
            SELECT * FROM trip_recommendations
            WHERE booked = 1 AND (passenger_id = %s OR passenger_id IS NULL)
        """
        excursions = query_all(excursions_sql, (passenger_id,))

        return {
            "passenger_id": passenger_id,
            "tickets": tickets,
            "booked_cars": cars,
            "booked_hotels": hotels,
            "booked_excursions": excursions,
        }

    @staticmethod
    def get_flights(
        departure: Optional[str] = None,
        arrival: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search available flights."""
        conditions = ["1=1"]
        params: list = []
        if departure:
            conditions.append("departure_airport = %s")
            params.append(departure.upper())
        if arrival:
            conditions.append("arrival_airport = %s")
            params.append(arrival.upper())

        sql = f"""
            SELECT * FROM flights
            WHERE {' AND '.join(conditions)}
            ORDER BY scheduled_departure
            LIMIT %s
        """
        params.append(limit)
        return query_all(sql, tuple(params))

    @staticmethod
    def get_car_rentals(location: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM car_rentals WHERE 1=1"
        params: list = []
        if location:
            sql += " AND location ILIKE %s"
            params.append(f"%{location}%")
        sql += " ORDER BY id"
        return query_all(sql, tuple(params))

    @staticmethod
    def get_hotels(location: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM hotels WHERE 1=1"
        params: list = []
        if location:
            sql += " AND location ILIKE %s"
            params.append(f"%{location}%")
        sql += " ORDER BY id"
        return query_all(sql, tuple(params))

    @staticmethod
    def get_trip_recommendations(location: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM trip_recommendations WHERE 1=1"
        params: list = []
        if location:
            sql += " AND location ILIKE %s"
            params.append(f"%{location}%")
        sql += " ORDER BY id"
        return query_all(sql, tuple(params))

    @staticmethod
    def get_database_stats() -> Dict[str, int]:
        """Return row counts for all main tables to power the live DB dashboard."""
        tables = [
            "aircrafts_data", "airports_data", "flights", "bookings",
            "tickets", "ticket_flights", "boarding_passes",
            "car_rentals", "hotels", "trip_recommendations",
            "chat_sessions", "chat_messages", "pending_actions",
        ]
        stats = {}
        with get_db() as conn:
            with conn.cursor() as cur:
                for t in tables:
                    try:
                        cur.execute(f"SELECT count(*) FROM {t};")
                        stats[t] = cur.fetchone()[0]
                    except Exception:
                        stats[t] = 0
        return stats

    @staticmethod
    def save_chat_message(
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        passenger_id: Optional[str] = None,
    ) -> int:
        """Save a message into chat_messages table, ensuring session exists."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (session_id, passenger_id)
                    VALUES (%s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW()
                    """,
                    (session_id, passenger_id or "unknown"),
                )
                cur.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, content, tool_calls)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (session_id, role, content, json.dumps(tool_calls or [])),
                )
                conn.commit()
                return cur.fetchone()[0]

    @staticmethod
    def get_chat_messages(session_id: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT id, session_id, role, content, tool_calls, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC, id ASC
        """
        return query_all(sql, (session_id,))

    @staticmethod
    def create_pending_action(
        action_id: str,
        session_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        description: str,
    ) -> None:
        sql = """
            INSERT INTO pending_actions (action_id, session_id, tool_name, tool_args, description, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            ON CONFLICT (action_id) DO UPDATE SET
                tool_name = EXCLUDED.tool_name,
                tool_args = EXCLUDED.tool_args,
                description = EXCLUDED.description,
                status = 'pending'
        """
        execute_mutation(sql, (action_id, session_id, tool_name, json.dumps(tool_args), description))

    @staticmethod
    def get_pending_action(action_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM pending_actions WHERE action_id = %s"
        return query_one(sql, (action_id,))

    @staticmethod
    def update_pending_action_status(action_id: str, status: str) -> None:
        sql = "UPDATE pending_actions SET status = %s WHERE action_id = %s"
        execute_mutation(sql, (status, action_id))
