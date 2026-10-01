import type {
  Passenger,
  PassengerOverview,
  FlightItem,
  BookedItem,
  DatabaseStats,
} from './types';

const API_BASE = '/api';

export async function checkHealth(): Promise<{
  status: string;
  database: string;
  model: string;
  table_stats: DatabaseStats;
}> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function getPassengers(): Promise<Passenger[]> {
  const res = await fetch(`${API_BASE}/passengers`);
  if (!res.ok) throw new Error('Failed to load passengers');
  const data = await res.json();
  return data.passengers || [];
}

export async function getPassengerOverview(passengerId: string): Promise<PassengerOverview> {
  const res = await fetch(`${API_BASE}/passengers/${encodeURIComponent(passengerId)}/overview`);
  if (!res.ok) throw new Error(`Failed to load passenger ${passengerId} overview`);
  return res.json();
}

export async function getFlights(departure?: string, arrival?: string, limit: number = 30): Promise<FlightItem[]> {
  const params = new URLSearchParams();
  if (departure) params.append('departure', departure);
  if (arrival) params.append('arrival', arrival);
  params.append('limit', limit.toString());

  const res = await fetch(`${API_BASE}/flights?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch flights');
  const data = await res.json();
  return data.flights || [];
}

export async function getCarRentals(location?: string): Promise<BookedItem[]> {
  const params = new URLSearchParams();
  if (location) params.append('location', location);
  const res = await fetch(`${API_BASE}/car-rentals?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch car rentals');
  const data = await res.json();
  return data.car_rentals || [];
}

export async function getHotels(location?: string): Promise<BookedItem[]> {
  const params = new URLSearchParams();
  if (location) params.append('location', location);
  const res = await fetch(`${API_BASE}/hotels?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch hotels');
  const data = await res.json();
  return data.hotels || [];
}

export async function getExcursions(location?: string): Promise<BookedItem[]> {
  const params = new URLSearchParams();
  if (location) params.append('location', location);
  const res = await fetch(`${API_BASE}/excursions?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch excursions');
  const data = await res.json();
  return data.excursions || [];
}

export async function getDatabaseStats(): Promise<DatabaseStats> {
  const res = await fetch(`${API_BASE}/database/stats`);
  if (!res.ok) throw new Error('Failed to fetch DB stats');
  const data = await res.json();
  return data.stats || {};
}

export async function reseedDatabase(): Promise<DatabaseStats> {
  const res = await fetch(`${API_BASE}/database/seed`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reseed database');
  const data = await res.json();
  return data.stats || {};
}

export async function sendChatMessage(payload: {
  passenger_id: string;
  thread_id: string;
  message: string;
  mode?: string;
}): Promise<{
  status: 'completed' | 'requires_approval';
  message: string;
  thread_id: string;
  mode?: string;
  tool_calls?: string[];
  action_id?: string;
  actions?: Array<{ name: string; args: Record<string, any>; description: string }>;
}> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const errorMsg =
      (typeof errorData.detail === 'string' && errorData.detail) ||
      (errorData.detail && errorData.detail.message) ||
      errorData.error ||
      errorData.message ||
      'Failed to send message';
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function approveAction(payload: {
  passenger_id: string;
  thread_id: string;
  action_id: string;
  approved: boolean;
  reason?: string;
  mode?: string;
}): Promise<{
  status: 'completed' | 'requires_approval';
  message: string;
  thread_id: string;
  mode?: string;
  tool_calls?: string[];
  action_id?: string;
  actions?: Array<{ name: string; args: Record<string, any>; description: string }>;
}> {
  const res = await fetch(`${API_BASE}/chat/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const errorMsg =
      (typeof errorData.detail === 'string' && errorData.detail) ||
      (errorData.detail && errorData.detail.message) ||
      errorData.error ||
      errorData.message ||
      'Failed to resolve action';
    throw new Error(errorMsg);
  }
  return res.json();
}
