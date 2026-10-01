import React, { useState } from 'react';
import {
  Plane,
  Ticket,
  Car,
  Building,
  MapPin,
  CheckCircle,
  Clock,
  QrCode,
  Search,
  BookOpen,
} from 'lucide-react';
import type { PassengerOverview, FlightItem, BookedItem } from '../types';

interface DashboardPanelProps {
  overview: PassengerOverview | null;
  flights: FlightItem[];
  carRentals?: BookedItem[];
  hotels?: BookedItem[];
  excursions?: BookedItem[];
  isLoading: boolean;
  onRefresh: () => void;
}

export const DashboardPanel: React.FC<DashboardPanelProps> = ({
  overview,
  flights,
  isLoading,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState<'itinerary' | 'services' | 'catalog' | 'policies'>('itinerary');
  const [flightSearchTerm, setFlightSearchTerm] = useState('');

  const primaryTicket = overview?.tickets?.[0];

  const filteredFlights = flights.filter(
    (f) =>
      f.flight_no.toLowerCase().includes(flightSearchTerm.toLowerCase()) ||
      f.departure_airport.toLowerCase().includes(flightSearchTerm.toLowerCase()) ||
      f.arrival_airport.toLowerCase().includes(flightSearchTerm.toLowerCase())
  );

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-800/80 bg-slate-900/60 shadow-2xl backdrop-blur-xl">
      {/* Tab Navigation Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 px-4 py-3 sm:px-6">
        <div className="flex space-x-1 sm:space-x-2">
          <button
            type="button"
            id="tab-itinerary-btn"
            onClick={() => setActiveTab('itinerary')}
            className={`flex items-center space-x-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition ${
              activeTab === 'itinerary'
                ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Ticket className="h-4 w-4" />
            <span>Itinerary</span>
          </button>

          <button
            type="button"
            id="tab-services-btn"
            onClick={() => setActiveTab('services')}
            className={`flex items-center space-x-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition ${
              activeTab === 'services'
                ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Building className="h-4 w-4" />
            <span>
              Bookings (
              {(overview?.booked_hotels?.length || 0) +
                (overview?.booked_cars?.length || 0) +
                (overview?.booked_excursions?.length || 0)}
              )
            </span>
          </button>

          <button
            type="button"
            id="tab-catalog-btn"
            onClick={() => setActiveTab('catalog')}
            className={`flex items-center space-x-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition ${
              activeTab === 'catalog'
                ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Plane className="h-4 w-4" />
            <span>Flight Catalog</span>
          </button>

          <button
            type="button"
            id="tab-policies-btn"
            onClick={() => setActiveTab('policies')}
            className={`flex items-center space-x-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition ${
              activeTab === 'policies'
                ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <BookOpen className="h-4 w-4" />
            <span>Policies</span>
          </button>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white"
          title="Refresh Itinerary from Neon DB"
        >
          <Clock className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {/* TAB 1: ITINERARY & BOARDING PASS */}
        {activeTab === 'itinerary' && (
          <div className="space-y-6">
            {primaryTicket ? (
              <div className="relative overflow-hidden rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-slate-900 via-slate-900/95 to-slate-950 p-6 shadow-2xl">
                {/* Background decorative glow */}
                <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-cyan-500/10 blur-3xl"></div>

                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 ring-1 ring-cyan-500/30">
                      <Plane className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-xs uppercase tracking-wider text-slate-400">
                        Boarding Pass • {primaryTicket.fare_conditions} Class
                      </div>
                      <div className="font-heading text-lg font-bold text-white">
                        {primaryTicket.passenger_name || 'Passenger'}
                      </div>
                    </div>
                  </div>
                  <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 ring-1 ring-emerald-500/20">
                    {primaryTicket.status}
                  </span>
                </div>

                {/* Route Section */}
                <div className="my-6 grid grid-cols-3 items-center text-center">
                  <div className="text-left">
                    <div className="text-3xl font-extrabold tracking-tight text-white">
                      {primaryTicket.departure_airport}
                    </div>
                    <div className="text-xs text-slate-400">Departure Airport</div>
                  </div>

                  <div className="flex flex-col items-center">
                    <span className="text-[11px] font-semibold text-cyan-400">
                      Flight {primaryTicket.flight_no}
                    </span>
                    <div className="relative my-2 flex w-full items-center justify-center">
                      <div className="h-0.5 w-full bg-slate-700"></div>
                      <Plane className="absolute h-4 w-4 text-cyan-400" />
                    </div>
                    <span className="text-[10px] text-slate-400">Non-stop</span>
                  </div>

                  <div className="text-right">
                    <div className="text-3xl font-extrabold tracking-tight text-white">
                      {primaryTicket.arrival_airport}
                    </div>
                    <div className="text-xs text-slate-400">Arrival Airport</div>
                  </div>
                </div>

                {/* Flight Metadata Grid */}
                <div className="grid grid-cols-2 gap-4 rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 sm:grid-cols-4">
                  <div>
                    <div className="text-[10px] uppercase text-slate-400">Date & Time</div>
                    <div className="text-xs font-semibold text-slate-200">
                      {new Date(primaryTicket.scheduled_departure).toLocaleDateString()}
                    </div>
                    <div className="text-[11px] text-cyan-400 font-mono">
                      {new Date(primaryTicket.scheduled_departure).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase text-slate-400">Seat</div>
                    <div className="font-mono text-base font-bold text-emerald-400">
                      {primaryTicket.seat_no || '14B'}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase text-slate-400">Boarding Group</div>
                    <div className="font-mono text-sm font-bold text-white">
                      Group {primaryTicket.boarding_no || '2'}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase text-slate-400">Booking Ref</div>
                    <div className="font-mono text-xs font-semibold text-cyan-300">
                      {primaryTicket.book_ref}
                    </div>
                  </div>
                </div>

                {/* Footer with barcode styling */}
                <div className="mt-5 flex items-center justify-between border-t border-slate-800 pt-4">
                  <div className="text-[11px] font-mono text-slate-500">
                    TICKET: {primaryTicket.ticket_no}
                  </div>
                  <div className="flex items-center space-x-2 text-cyan-400">
                    <QrCode className="h-6 w-6" />
                    <span className="text-[10px] uppercase tracking-wider text-slate-400">
                      Electronic E-Ticket Verified
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-800 p-8 text-center text-slate-400">
                No active ticket found for this passenger in Neon PostgreSQL.
              </div>
            )}

            {/* Additional flights on ticket */}
            {overview?.tickets && overview.tickets.length > 1 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  All Segments ({overview.tickets.length})
                </h4>
                {overview.tickets.map((t, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 transition hover:border-slate-700"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="rounded-lg bg-slate-800 p-2 text-cyan-400">
                        <Plane className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-white">
                          {t.departure_airport} → {t.arrival_airport} ({t.flight_no})
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {new Date(t.scheduled_departure).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[10px] font-medium text-slate-300">
                        {t.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: BOOKED SERVICES */}
        {activeTab === 'services' && (
          <div className="space-y-6">
            {/* Booked Hotels */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-heading text-sm font-bold text-white flex items-center space-x-2">
                  <Building className="h-4 w-4 text-cyan-400" />
                  <span>Reserved Hotels</span>
                </h3>
                <span className="text-xs text-slate-400">
                  {overview?.booked_hotels?.length || 0} active
                </span>
              </div>

              {overview?.booked_hotels && overview.booked_hotels.length > 0 ? (
                <div className="space-y-2">
                  {overview.booked_hotels.map((hotel) => (
                    <div
                      key={hotel.id}
                      className="rounded-xl border border-cyan-500/20 bg-slate-950/60 p-3.5"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-xs font-bold text-white">{hotel.name}</div>
                          <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                            <MapPin className="h-3 w-3 text-cyan-400" />
                            <span>{hotel.location}</span>
                            <span>•</span>
                            <span className="text-cyan-300">{hotel.price_tier}</span>
                          </div>
                        </div>
                        <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                          Confirmed
                        </span>
                      </div>
                      <div className="mt-2 flex items-center space-x-4 text-[11px] text-slate-400">
                        <div>Check-in: <span className="text-slate-200">{hotel.checkin_date}</span></div>
                        <div>Check-out: <span className="text-slate-200">{hotel.checkout_date}</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-4 text-center text-xs text-slate-400">
                  No hotel reservations booked yet. Ask AeroAssist to book one!
                </div>
              )}
            </div>

            {/* Booked Cars */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-heading text-sm font-bold text-white flex items-center space-x-2">
                  <Car className="h-4 w-4 text-blue-400" />
                  <span>Rental Cars</span>
                </h3>
                <span className="text-xs text-slate-400">
                  {overview?.booked_cars?.length || 0} active
                </span>
              </div>

              {overview?.booked_cars && overview.booked_cars.length > 0 ? (
                <div className="space-y-2">
                  {overview.booked_cars.map((car) => (
                    <div
                      key={car.id}
                      className="rounded-xl border border-blue-500/20 bg-slate-950/60 p-3.5"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-xs font-bold text-white">{car.name}</div>
                          <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                            <MapPin className="h-3 w-3 text-blue-400" />
                            <span>{car.location}</span>
                            <span>•</span>
                            <span className="text-blue-300">{car.price_tier}</span>
                          </div>
                        </div>
                        <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                          Reserved
                        </span>
                      </div>
                      <div className="mt-2 flex items-center space-x-4 text-[11px] text-slate-400">
                        <div>Pickup: <span className="text-slate-200">{car.start_date}</span></div>
                        <div>Return: <span className="text-slate-200">{car.end_date}</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-4 text-center text-xs text-slate-400">
                  No car rentals booked yet.
                </div>
              )}
            </div>

            {/* Booked Excursions */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-heading text-sm font-bold text-white flex items-center space-x-2">
                  <MapPin className="h-4 w-4 text-emerald-400" />
                  <span>Excursions & Activities</span>
                </h3>
                <span className="text-xs text-slate-400">
                  {overview?.booked_excursions?.length || 0} active
                </span>
              </div>

              {overview?.booked_excursions && overview.booked_excursions.length > 0 ? (
                <div className="space-y-2">
                  {overview.booked_excursions.map((trip) => (
                    <div
                      key={trip.id}
                      className="rounded-xl border border-emerald-500/20 bg-slate-950/60 p-3.5"
                    >
                      <div className="text-xs font-bold text-white">{trip.name}</div>
                      <div className="text-[11px] text-slate-400">{trip.details}</div>
                      <div className="mt-2 flex items-center space-x-2 text-[10px] text-emerald-400">
                        <CheckCircle className="h-3 w-3" />
                        <span>Tour Voucher Ready</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-4 text-center text-xs text-slate-400">
                  No excursions booked. Ask for trip recommendations!
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: FLIGHT CATALOG */}
        {activeTab === 'catalog' && (
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by flight number or airport (BSL, CDG, ZRH)..."
                value={flightSearchTerm}
                onChange={(e) => setFlightSearchTerm(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 py-2 pl-9 pr-4 text-xs text-white placeholder-slate-500 outline-none focus:border-cyan-500"
              />
            </div>

            <div className="space-y-2">
              {filteredFlights.slice(0, 20).map((flight) => (
                <div
                  key={flight.flight_id}
                  className="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/60 p-3 text-xs transition hover:border-slate-700"
                >
                  <div>
                    <div className="flex items-center space-x-2 font-semibold text-white">
                      <span className="font-mono text-cyan-400">{flight.flight_no}</span>
                      <span>•</span>
                      <span>
                        {flight.departure_airport} → {flight.arrival_airport}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Departs: {new Date(flight.scheduled_departure).toLocaleString()}
                    </div>
                  </div>
                  <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300">
                    ID #{flight.flight_id}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: POLICIES */}
        {activeTab === 'policies' && (
          <div className="space-y-4 text-xs text-slate-300">
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <h4 className="font-heading text-sm font-bold text-cyan-400 mb-1">
                Ticket Changes & Cancellations
              </h4>
              <p className="leading-relaxed text-slate-300">
                Changes can be made up to 3 hours prior to scheduled departure.
                Economy tickets are subject to a standard change fee plus fare difference.
                Business Class tickets allow complimentary flight adjustments.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <h4 className="font-heading text-sm font-bold text-cyan-400 mb-1">
                Baggage Allowance Policy
              </h4>
              <p className="leading-relaxed text-slate-300">
                All passengers are entitled to 1 carry-on bag (up to 8 kg) and 1 personal item.
                Checked baggage allowance is 1 bag (up to 23 kg) for Economy, and 2 bags (up to 32 kg)
                for Business Class.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <h4 className="font-heading text-sm font-bold text-cyan-400 mb-1">
                Partner Services (Hotels & Car Rentals)
              </h4>
              <p className="leading-relaxed text-slate-300">
                Partner hotel and car reservations can be booked directly through AeroAssist
                with your airline booking reference. Cancellations are free up to 24 hours
                before pickup or check-in.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
