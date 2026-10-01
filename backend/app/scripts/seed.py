"""Database initialization and seeding script for Neon PostgreSQL.

Populates tables with schema and realistic sample data for the airline customer support bot.
"""

from __future__ import annotations

import datetime
import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_batch

from ..config import DATABASE_URL, BACKEND_DIR

SQLITE_DB_PATH = str(BACKEND_DIR / "data" / "travel2.sqlite")


def get_pg_connection():
    return psycopg2.connect(DATABASE_URL)


def create_schema(conn):
    with conn.cursor() as cur:
        print("Creating PostgreSQL tables...")
        cur.execute(
            """
            -- Core airline data
            CREATE TABLE IF NOT EXISTS aircrafts_data (
                aircraft_code VARCHAR(10) PRIMARY KEY,
                model TEXT NOT NULL,
                range INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS airports_data (
                airport_code VARCHAR(10) PRIMARY KEY,
                airport_name TEXT NOT NULL,
                city TEXT NOT NULL,
                coordinates TEXT,
                timezone TEXT
            );

            CREATE TABLE IF NOT EXISTS flights (
                flight_id INTEGER PRIMARY KEY,
                flight_no VARCHAR(20) NOT NULL,
                scheduled_departure TIMESTAMPTZ NOT NULL,
                scheduled_arrival TIMESTAMPTZ NOT NULL,
                departure_airport VARCHAR(10) NOT NULL,
                arrival_airport VARCHAR(10) NOT NULL,
                status VARCHAR(30) NOT NULL,
                aircraft_code VARCHAR(10),
                actual_departure TIMESTAMPTZ,
                actual_arrival TIMESTAMPTZ
            );

            CREATE TABLE IF NOT EXISTS bookings (
                book_ref VARCHAR(10) PRIMARY KEY,
                book_date TIMESTAMPTZ NOT NULL,
                total_amount NUMERIC(10, 2) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tickets (
                ticket_no VARCHAR(20) PRIMARY KEY,
                book_ref VARCHAR(10) NOT NULL,
                passenger_id VARCHAR(30) NOT NULL,
                passenger_name TEXT NOT NULL,
                contact_data JSONB
            );

            CREATE TABLE IF NOT EXISTS ticket_flights (
                ticket_no VARCHAR(20) NOT NULL,
                flight_id INTEGER NOT NULL,
                fare_conditions VARCHAR(20) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                PRIMARY KEY (ticket_no, flight_id)
            );

            CREATE TABLE IF NOT EXISTS boarding_passes (
                ticket_no VARCHAR(20) NOT NULL,
                flight_id INTEGER NOT NULL,
                boarding_no INTEGER NOT NULL,
                seat_no VARCHAR(10) NOT NULL,
                PRIMARY KEY (ticket_no, flight_id)
            );

            -- Auxiliary travel services
            CREATE TABLE IF NOT EXISTS car_rentals (
                id SERIAL PRIMARY KEY,
                location TEXT NOT NULL,
                name TEXT NOT NULL,
                price_tier TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                booked BOOLEAN DEFAULT FALSE,
                passenger_id VARCHAR(30)
            );

            CREATE TABLE IF NOT EXISTS hotels (
                id SERIAL PRIMARY KEY,
                location TEXT NOT NULL,
                name TEXT NOT NULL,
                price_tier TEXT NOT NULL,
                checkin_date DATE NOT NULL,
                checkout_date DATE NOT NULL,
                booked BOOLEAN DEFAULT FALSE,
                passenger_id VARCHAR(30)
            );

            CREATE TABLE IF NOT EXISTS trip_recommendations (
                id SERIAL PRIMARY KEY,
                location TEXT NOT NULL,
                name TEXT NOT NULL,
                details TEXT NOT NULL,
                booked BOOLEAN DEFAULT FALSE,
                passenger_id VARCHAR(30)
            );

            -- Human-in-the-Loop & Chat session persistence
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id VARCHAR(64) PRIMARY KEY,
                passenger_id VARCHAR(30) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'::jsonb
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                tool_calls JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS pending_actions (
                id VARCHAR(64) PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                tool_name VARCHAR(64) NOT NULL,
                tool_args JSONB NOT NULL,
                description TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                resolved_at TIMESTAMPTZ
            );
        """
        )
    conn.commit()


def seed_data(conn):
    print("Reading data from travel2.sqlite ...")
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Warning: {SQLITE_DB_PATH} not found. Skipping sqlite imports.")
        return

    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cur = sqlite_conn.cursor()

    now = datetime.datetime.now(datetime.timezone.utc)
    base_departure = now + datetime.timedelta(hours=2)

    with conn.cursor() as cur:
        # Aircrafts
        sqlite_cur.execute("SELECT aircraft_code, model, range FROM aircrafts_data;")
        aircrafts = sqlite_cur.fetchall()
        execute_batch(
            cur,
            "INSERT INTO aircrafts_data (aircraft_code, model, range) VALUES (%s, %s, %s) ON CONFLICT (aircraft_code) DO UPDATE SET model=EXCLUDED.model, range=EXCLUDED.range",
            aircrafts,
        )

        # Airports
        sqlite_cur.execute(
            "SELECT airport_code, airport_name, city, coordinates, timezone FROM airports_data;"
        )
        airports = sqlite_cur.fetchall()
        execute_batch(
            cur,
            "INSERT INTO airports_data (airport_code, airport_name, city, coordinates, timezone) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (airport_code) DO NOTHING",
            airports,
        )

        # Sample flights
        sqlite_cur.execute(
            "SELECT flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code FROM flights LIMIT 120;"
        )
        sqlite_flights = sqlite_cur.fetchall()
        flights = []
        for i, f in enumerate(sqlite_flights):
            dep_time = base_departure + datetime.timedelta(days=(i % 7), hours=(i % 12))
            arr_time = dep_time + datetime.timedelta(hours=2, minutes=30)
            flights.append(
                (f[0], f[1], dep_time, arr_time, f[4], f[5], "Scheduled", f[7])
            )

        execute_batch(
            cur,
            "INSERT INTO flights (flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (flight_id) DO UPDATE SET scheduled_departure=EXCLUDED.scheduled_departure, scheduled_arrival=EXCLUDED.scheduled_arrival",
            flights,
        )

        # Car rentals
        cars = [
            ("Basel", "Sixt Premium Sedan", "Luxury", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Basel", "Europcar Compact SUV", "Mid-tier", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=4)).date(), False, None),
            ("Basel", "Hertz Eco Electric", "Economy", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=6)).date(), False, None),
            ("Zurich", "Avis Executive BMW", "Luxury", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=7)).date(), False, None),
            ("Zurich", "Sixt Convertible", "Luxury", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Zurich", "Budget City Hatchback", "Economy", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=3)).date(), False, None),
            ("Paris", "Hertz French Classic", "Economy", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Paris", "Sixt Paris Sport", "Luxury", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=6)).date(), False, None),
            ("Geneva", "Europcar Alpine 4x4", "Mid-tier", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=4)).date(), False, None),
            ("Geneva", "Swiss Mobility EV", "Economy", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Bern", "Hertz Swiss Cruiser", "Mid-tier", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Bern", "Sixt Capital Sedan", "Luxury", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=4)).date(), False, None),
        ]
        cur.execute("TRUNCATE TABLE car_rentals RESTART IDENTITY CASCADE;")
        execute_batch(
            cur,
            "INSERT INTO car_rentals (location, name, price_tier, start_date, end_date, booked, passenger_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            cars,
        )

        # Hotels
        hotels = [
            ("Basel", "Grand Hotel Les Trois Rois", "Luxury (5-star)", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=4)).date(), False, None),
            ("Basel", "Hotel Victoria Central", "Mid-tier", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=3)).date(), False, None),
            ("Basel", "Ibis Styles Basel City", "Economy", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Zurich", "The Dolder Grand Resort", "Luxury (5-star)", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=4)).date(), False, None),
            ("Zurich", "Baur au Lac", "Luxury (5-star)", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=6)).date(), False, None),
            ("Zurich", "CitizenM Zurich Center", "Mid-tier", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=3)).date(), False, None),
            ("Paris", "Le Meurice Palace", "Luxury (5-star)", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Paris", "Novotel Paris Tour Eiffel", "Mid-tier", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=4)).date(), False, None),
            ("Geneva", "Four Seasons Hotel des Bergues", "Luxury (5-star)", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=4)).date(), False, None),
            ("Geneva", "Hotel d'Angleterre", "Luxury (5-star)", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
            ("Bern", "Hotel Schweizerhof Bern & Spa", "Luxury (5-star)", (now + datetime.timedelta(days=1)).date(), (now + datetime.timedelta(days=3)).date(), False, None),
            ("Bern", "Kreuz Bern Hotel", "Mid-tier", (now + datetime.timedelta(days=2)).date(), (now + datetime.timedelta(days=5)).date(), False, None),
        ]
        cur.execute("TRUNCATE TABLE hotels RESTART IDENTITY CASCADE;")
        execute_batch(
            cur,
            "INSERT INTO hotels (location, name, price_tier, checkin_date, checkout_date, booked, passenger_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            hotels,
        )

        # Excursions
        excursions = [
            ("Basel", "Rhine River Sunset Cruise", "Panoramic evening boat tour on the Rhine with complimentary Swiss fondue and wine tasting.", False, None),
            ("Basel", "Old Town Walking & Architecture Tour", "2-hour guided walking tour exploring Basel Minster, Rathaus, and contemporary Herzog & de Meuron architecture.", False, None),
            ("Basel", "Art Basel Foundation Tour", "Exclusive VIP private tour through the Fondation Beyeler modern art collection.", False, None),
            ("Zurich", "Lake Zurich Catamaran Tour", "1.5-hour smooth sailing catamaran cruise across Lake Zurich with views of the Swiss Alps.", False, None),
            ("Zurich", "Uetliberg Mountain Cable & Fondue Experience", "Top of Zurich excursion with cable car transit and authentic mountain summit dining.", False, None),
            ("Zurich", "Lindt Home of Chocolate Tasting", "Interactive chocolate museum visit with chocolate masterclass and fountain tasting.", False, None),
            ("Paris", "Louvre Museum Private Highlights", "Fast-track access and 3-hour private curator-led tour of the Mona Lisa and classic masterworks.", False, None),
            ("Paris", "Seine Dinner & Jazz River Cruise", "3-course gourmet dinner cruise along the illuminated Eiffel Tower and Notre-Dame.", False, None),
            ("Geneva", "Lake Geneva Private Yacht & Jet d'Eau", "Private 2-hour skippered luxury boat tour around Jet d'Eau and Mont Salève.", False, None),
            ("Bern", "Aare River Walk & Bear Park Excursion", "Guided walking trail along the Aare River visiting UNESCO Old Town and the Bear Park.", False, None),
        ]
        cur.execute("TRUNCATE TABLE trip_recommendations RESTART IDENTITY CASCADE;")
        execute_batch(
            cur,
            "INSERT INTO trip_recommendations (location, name, details, booked, passenger_id) VALUES (%s, %s, %s, %s, %s)",
            excursions,
        )

        # Test bookings for passenger 3442 587242 (Luca Mueller)
        bookings = [
            ("C72401", now - datetime.timedelta(days=10), 1250.00),
            ("C72402", now - datetime.timedelta(days=5), 890.00),
            ("C72403", now - datetime.timedelta(days=2), 2100.00),
            ("C72404", now - datetime.timedelta(days=1), 540.00),
        ]
        execute_batch(
            cur,
            "INSERT INTO bookings (book_ref, book_date, total_amount) VALUES (%s, %s, %s) ON CONFLICT (book_ref) DO UPDATE SET total_amount=EXCLUDED.total_amount",
            bookings,
        )

        # Tickets
        tickets = [
            ("7240005432906569", "C72401", "3442 587242", "LUCA MUELLER", '{"phone": "+41 79 123 45 67", "email": "luca.mueller@example.ch"}'),
            ("7240005432906570", "C72402", "3442 587242", "LUCA MUELLER", '{"phone": "+41 79 123 45 67", "email": "luca.mueller@example.ch"}'),
            ("7240005432906571", "C72403", "9876 543210", "ELENA ROSTOVA", '{"phone": "+41 79 987 65 43", "email": "elena.rostova@example.ch"}'),
            ("7240005432906572", "C72404", "1122 334455", "MARC DUBOIS", '{"phone": "+33 6 12 34 56 78", "email": "marc.dubois@example.fr"}'),
        ]
        execute_batch(
            cur,
            "INSERT INTO tickets (ticket_no, book_ref, passenger_id, passenger_name, contact_data) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (ticket_no) DO UPDATE SET passenger_name=EXCLUDED.passenger_name",
            tickets,
        )

        # Ticket flights
        ticket_flights = [
            ("7240005432906569", 1459, "Economy", 450.00),
            ("7240005432906569", 19250, "Economy", 400.00),
            ("7240005432906570", 2001, "Business", 890.00),
            ("7240005432906571", 3001, "First", 2100.00),
            ("7240005432906572", 4001, "Economy", 540.00),
        ]
        execute_batch(
            cur,
            "INSERT INTO ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES (%s, %s, %s, %s) ON CONFLICT (ticket_no, flight_id) DO NOTHING",
            ticket_flights,
        )

        # Boarding passes
        boarding_passes = [
            ("7240005432906569", 1459, 42, "14B"),
            ("7240005432906569", 19250, 18, "12A"),
            ("7240005432906570", 2001, 7, "2K"),
            ("7240005432906571", 3001, 1, "1A"),
            ("7240005432906572", 4001, 35, "22C"),
        ]
        execute_batch(
            cur,
            "INSERT INTO boarding_passes (ticket_no, flight_id, boarding_no, seat_no) VALUES (%s, %s, %s, %s) ON CONFLICT (ticket_no, flight_id) DO NOTHING",
            boarding_passes,
        )

    conn.commit()
    sqlite_conn.close()
    print("Data seeded successfully!")


def run_migration():
    print(f"Connecting to Neon PostgreSQL at {DATABASE_URL.split('@')[-1]} ...")
    conn = get_pg_connection()
    try:
        create_schema(conn)
        seed_data(conn)
        with conn.cursor() as cur:
            tables = [
                "aircrafts_data", "airports_data", "flights", "bookings",
                "tickets", "ticket_flights", "boarding_passes",
                "car_rentals", "hotels", "trip_recommendations"
            ]
            print("\n=== POSTGRESQL VERIFICATION SUMMARY ===")
            for t in tables:
                cur.execute(f"SELECT count(*) FROM {t};")
                print(f"  {t}: {cur.fetchone()[0]} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
