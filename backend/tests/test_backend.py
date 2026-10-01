"""Unit and integration tests for the FastAPI backend, database service, and LangChain tools."""

import sys
import unittest
from pathlib import Path

# Add customer_support_app directory to path
app_root = str(Path(__file__).resolve().parent.parent.parent)
if app_root not in sys.path:
    sys.path.insert(0, app_root)

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import DatabaseService
from backend.app.rag import PolicyRetriever


class TestDatabaseService(unittest.TestCase):
    """Test suite for database access layer."""

    def test_get_database_stats(self):
        stats = DatabaseService.get_database_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("flights", stats)
        self.assertIn("aircrafts_data", stats)
        self.assertGreater(stats["flights"], 0)

    def test_get_passengers(self):
        passengers = DatabaseService.get_passengers()
        self.assertIsInstance(passengers, list)
        self.assertGreater(len(passengers), 0)
        passenger_ids = [p["passenger_id"] for p in passengers]
        self.assertIn("3442 587242", passenger_ids)

    def test_get_passenger_overview(self):
        overview = DatabaseService.get_passenger_overview("3442 587242")
        self.assertEqual(overview["passenger_id"], "3442 587242")
        self.assertIn("tickets", overview)
        self.assertGreater(len(overview["tickets"]), 0)

    def test_get_flights_filter(self):
        flights = DatabaseService.get_flights(departure="BSL", limit=5)
        self.assertIsInstance(flights, list)
        for f in flights:
            self.assertEqual(f["departure_airport"], "BSL")

    def test_get_car_rentals(self):
        cars = DatabaseService.get_car_rentals()
        self.assertIsInstance(cars, list)
        self.assertGreater(len(cars), 0)

    def test_get_hotels(self):
        hotels = DatabaseService.get_hotels()
        self.assertIsInstance(hotels, list)
        self.assertGreater(len(hotels), 0)

    def test_trip_recommendations(self):
        trips = DatabaseService.get_trip_recommendations()
        self.assertIsInstance(trips, list)
        self.assertGreater(len(trips), 0)


class TestPolicyRetriever(unittest.TestCase):
    """Test suite for policy RAG retriever."""

    def setUp(self):
        self.retriever = PolicyRetriever()

    def test_retriever_query(self):
        results = self.retriever.query("What is the baggage allowance for economy tickets?", k=2)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertTrue(hasattr(results[0], "text"))
        self.assertTrue(len(results[0].text) > 0)


class TestFastAPI(unittest.TestCase):
    """Integration test suite for FastAPI REST API endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("Neon PostgreSQL", data["database"])

    def test_passengers_endpoint(self):
        response = self.client.get("/api/passengers")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("passengers", data)
        self.assertGreater(len(data["passengers"]), 0)

    def test_passenger_overview_endpoint(self):
        response = self.client.get("/api/passengers/3442%20587242/overview")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["passenger_id"], "3442 587242")

    def test_flights_endpoint(self):
        response = self.client.get("/api/flights?limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("flights", data)

    def test_catalog_endpoints(self):
        for endpoint, key in [
            ("/api/car-rentals", "car_rentals"),
            ("/api/hotels", "hotels"),
            ("/api/excursions", "excursions"),
            ("/api/database/stats", "stats"),
        ]:
            resp = self.client.get(endpoint)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(key, resp.json())

    def test_chat_validation(self):
        # Empty message error (400 HTTPException)
        response = self.client.post("/api/chat", json={"message": "", "passenger_id": "3442 587242"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
