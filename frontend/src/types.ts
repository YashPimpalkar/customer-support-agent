export interface Passenger {
  passenger_id: string;
  passenger_name: string | null;
  ticket_no: string | null;
  flight_no: string | null;
  departure_airport: string | null;
  arrival_airport: string | null;
  scheduled_departure: string | null;
  status: string | null;
}

export interface TicketFlight {
  ticket_no: string;
  book_ref: string;
  passenger_id: string;
  passenger_name: string | null;
  flight_id: number;
  flight_no: string;
  departure_airport: string;
  arrival_airport: string;
  scheduled_departure: string;
  scheduled_arrival: string;
  status: string;
  seat_no: string | null;
  boarding_no: number | null;
  fare_conditions: string;
  amount: number;
}

export interface BookedItem {
  id: number;
  name: string;
  location: string;
  price_tier?: string;
  start_date?: string;
  end_date?: string;
  checkin_date?: string;
  checkout_date?: string;
  keywords?: string;
  details?: string;
  booked: number;
  passenger_id?: string | null;
}

export interface PassengerOverview {
  passenger_id: string;
  tickets: TicketFlight[];
  booked_cars: BookedItem[];
  booked_hotels: BookedItem[];
  booked_excursions: BookedItem[];
}

export interface FlightItem {
  flight_id: number;
  flight_no: string;
  scheduled_departure: string;
  scheduled_arrival: string;
  departure_airport: string;
  arrival_airport: string;
  status: string;
  aircraft_code: string | null;
}

export interface PendingAction {
  name: string;
  args: Record<string, any>;
  description: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  toolCalls?: string[];
  pendingAction?: {
    actionId: string;
    actions: PendingAction[];
  };
  createdAt: string;
  status?: 'sending' | 'completed' | 'pending_approval';
}

export interface DatabaseStats {
  aircrafts_data: number;
  airports_data: number;
  flights: number;
  bookings: number;
  tickets: number;
  ticket_flights: number;
  boarding_passes: number;
  car_rentals: number;
  hotels: number;
  trip_recommendations: number;
  chat_sessions?: number;
  chat_messages?: number;
  pending_actions?: number;
  [key: string]: number | undefined;
}
