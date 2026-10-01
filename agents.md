# 🤖 AeroAssist Agent Ecosystem & Specification (`agents.md`)

This document defines the agent architecture, roles, state definitions, tool assignments, delegation transitions, and Human-in-the-Loop (HITL) authorization protocols across the **AeroAssist** airline customer support system.

---

## 🌟 Executive Summary

AeroAssist implements a multi-tier agent progression powered by **LangGraph** and **Google Gemini** (Gemini 3.8 Flash), connected to **Neon PostgreSQL** and augmented with **Policy RAG retrieval**:

| Architecture | Name | Routing Paradigm | Human Approval Mechanism |
| :--- | :--- | :--- | :--- |
| **Part 1** | Zero-Shot Agent | Single conversational agent with all 14 tools | ❌ No approval; all tools execute immediately |
| **Part 2** | Full Confirmation Agent | Single conversational agent with all 14 tools | ⚠️ Pause & interrupt before **every** tool execution |
| **Part 3** | Conditional Interrupt Agent | Single concierge with dual safe/sensitive routing | 🛡️ Safe tools run automatically; sensitive tools pause for HITL |
| **Part 4** | Specialized Multi-Agent Swarm | Primary router concierge + 4 specialized domain agents | 👑 Domain-isolated tools with conditional HITL interrupts per specialist |

---

## 🏗️ Core Shared State Definitions

### 1. `AgentState` (Part 1, 2, and 3)
```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str  # Hydrated flight & passenger profile from database
```

### 2. `Part4State` (Part 4 Multi-Agent Swarm)
```python
def update_dialog_stack(left: list[str], right: str | None) -> list[str]:
    """Pushes new domain agent or pops returning to primary assistant."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class Part4State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[list[str], update_dialog_stack]
```

---

## 👥 Agent Directory (Part 4 Specialized Swarm)

```
                            ┌────────────────────────┐
                            │    Passenger Input     │
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │   fetch_user_info      │
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                 ┌─────────►│   Primary Assistant    │◄──────────┐
                 │          │  (Concierge & Router)  │           │
                 │          └───────────┬────────────┘           │
                 │                      │                        │
         CompleteOrEscalate             │ Delegation             │ CompleteOrEscalate
                 │                      ▼                        │
         ┌───────┴────────┬─────────────────────┬──────────────┬─┴──────────┐
         │                │                     │              │            │
         ▼                ▼                     ▼              ▼            ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Flight Updates │ │   Car Rental   │ │ Hotel Booking  │ │   Excursions   │
│   Specialist   │ │   Specialist   │ │   Specialist   │ │   Specialist   │
└────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
```

---

### 1. Primary Assistant (`primary_assistant`)
- **Role**: General concierge, inquiry triage, policy consultant, and routing dispatcher.
- **Responsibilities**:
  - Greet passenger and explain system capabilities.
  - Answer general flight status queries and airline policies.
  - Detect intent for bookings or modifications and delegate to the designated specialist.
- **Read-Only / Safe Tools**:
  - `fetch_user_flight_information()`: Look up passenger details and active ticket itineraries.
  - `search_flights(departure_airport, arrival_airport, start_time, end_time, limit)`: Search available scheduled flights.
  - `lookup_policy(query)`: RAG vector semantic search over airline regulations and fare policies.
- **Delegation Hand-Off Tools**:
  - `ToFlightBookingAssistant(location, request)`: Route to Flight Updates Specialist.
  - `ToBookCarRental(location, start_date, end_date, request)`: Route to Car Rental Specialist.
  - `ToHotelBookingAssistant(location, checkin_date, checkout_date, request)`: Route to Hotel Booking Specialist.
  - `ToBookExcursion(location, date, request)`: Route to Excursion Specialist.

---

### 2. Flight Updates Specialist (`update_flight`)
- **Role**: Manages flight rescheduling, seat re-assignments, and ticket cancellations.
- **Node Identifier**: `update_flight`
- **Safe Tools** (Execute Automatically):
  - `fetch_user_flight_information()`
  - `search_flights()`
- **Sensitive Tools** (Trigger HITL Approval Interrupt):
  - `update_ticket_to_new_flight(ticket_no, new_flight_id)`: Reassign passenger ticket to a different flight.
  - `cancel_ticket(ticket_no)`: Cancel ticket booking and release assigned seat.
- **Escalation Tool**:
  - `CompleteOrEscalate(reason)`: Relinquish control and pop dialog state back to Primary Assistant.

---

### 3. Car Rental Specialist (`book_car_rental`)
- **Role**: Searches rental fleets and manages reservations in destination cities.
- **Node Identifier**: `book_car_rental`
- **Safe Tools** (Execute Automatically):
  - `search_car_rentals(location, name, price_tier, start_date, end_date)`: Search fleet in Basel, Zurich, Paris, etc.
- **Sensitive Tools** (Trigger HITL Approval Interrupt):
  - `book_car_rental(rental_id)`: Book vehicle for passenger and mark as reserved.
  - `cancel_car_rental(rental_id)`: Cancel active vehicle reservation.
- **Escalation Tool**:
  - `CompleteOrEscalate(reason)`: Return control to Primary Assistant.

---

### 4. Hotel Booking Specialist (`book_hotel`)
- **Role**: Locates partner accommodations and manages hotel room reservations.
- **Node Identifier**: `book_hotel`
- **Safe Tools** (Execute Automatically):
  - `search_hotels(location, name, price_tier, checkin_date, checkout_date)`: Search partner hotels.
- **Sensitive Tools** (Trigger HITL Approval Interrupt):
  - `book_hotel(hotel_id)`: Confirm room booking for passenger.
  - `cancel_hotel(hotel_id)`: Cancel hotel room booking.
- **Escalation Tool**:
  - `CompleteOrEscalate(reason)`: Return control to Primary Assistant.

---

### 5. Excursion Specialist (`book_excursion`)
- **Role**: Recommends destination tours, cultural activities, and books excursion passes.
- **Node Identifier**: `book_excursion`
- **Safe Tools** (Execute Automatically):
  - `search_trip_recommendations(location, name, keywords)`: Search guided activities and experiences.
- **Sensitive Tools** (Trigger HITL Approval Interrupt):
  - `book_excursion(recommendation_id)`: Confirm booking for tour or activity.
  - `cancel_excursion(recommendation_id)`: Cancel excursion reservation.
- **Escalation Tool**:
  - `CompleteOrEscalate(reason)`: Return control to Primary Assistant.

---

## 🛡️ Tool Safety Matrix

| Tool Name | Scope | Classification | Requires Passenger Approval |
| :--- | :--- | :--- | :---: |
| `lookup_policy` | Policy RAG | **Safe** | ❌ No |
| `fetch_user_flight_information` | Core DB | **Safe** | ❌ No |
| `search_flights` | Core DB | **Safe** | ❌ No |
| `search_car_rentals` | Fleet DB | **Safe** | ❌ No |
| `search_hotels` | Partner DB | **Safe** | ❌ No |
| `search_trip_recommendations` | Tours DB | **Safe** | ❌ No |
| `update_ticket_to_new_flight` | Core DB | **Sensitive** | ✅ **Yes** |
| `cancel_ticket` | Core DB | **Sensitive** | ✅ **Yes** |
| `book_car_rental` | Fleet DB | **Sensitive** | ✅ **Yes** |
| `cancel_car_rental` | Fleet DB | **Sensitive** | ✅ **Yes** |
| `book_hotel` | Partner DB | **Sensitive** | ✅ **Yes** |
| `cancel_hotel` | Partner DB | **Sensitive** | ✅ **Yes** |
| `book_excursion` | Tours DB | **Sensitive** | ✅ **Yes** |
| `cancel_excursion` | Tours DB | **Sensitive** | ✅ **Yes** |

---

## 🔄 Human-in-the-Loop (HITL) Execution Protocol

```
Passenger Query ──► Agent generates ToolCall
                          │
            Is tool marked SENSITIVE?
              ├───────────┴───────────┐
             No                      Yes
              │                       │
      Execute ToolNode          Pause Graph Execution
              │                 (Interrupt before node)
              │                       │
      Return result to AI       Persist pending action in DB
              │                       │
     Generate AI answer         Present Approval Card to User
                                      │
                         ┌────────────┴────────────┐
                      Approve                    Deny
                         │                         │
                 Resume stream(None)       Inject ToolMessage
                         │                 ("Action denied by passenger")
                         │                         │
                  Execute tool             Resume stream(None)
                         │                         │
                 Generate AI answer        Agent adjusts course
```

1. **Detection**: LangGraph conditional edge routes sensitive calls to a dedicated sensitive node (`interrupt_before=[...]`).
2. **State Freezing**: LangGraph saves the execution checkpoint to `MemorySaver` (`thread_id`).
3. **Database Audit**: `AgentManager` inserts pending action record into `pending_actions` table.
4. **Interactive UI Card**: The React frontend renders an authorization card with action details, parameters, and two buttons: **Approve** and **Deny**.
5. **Resolution**:
   - **Approved**: API triggers `graph.stream(None, config)` to continue execution with tool output.
   - **Denied**: API triggers `graph.update_state()` injecting a `ToolMessage` informing the agent that the action was rejected with an optional passenger reason, allowing the agent to recommend alternatives.

---

## 🎯 Input Options & Test Scenarios per Agent Mode

The frontend UI provides dynamic, tailored input options and quick-action presets for each active agent mode:

### 1. Part 1: Zero-Shot Direct Execution (`part1`)
Designed to demonstrate immediate execution of both read queries and write mutations without human-in-the-loop interruptions:

| Preset Input Option | Category | Expected Behavior & Assertion |
| :--- | :--- | :--- |
| `"What flights do I have booked right now?"` | Safe Query | Reads passenger tickets directly from Neon PostgreSQL and returns flight LX0002. |
| `"Search available flights departing from Basel (BSL) to Paris (CDG)"` | Schedule Search | Queries live scheduled flights in database (returns flight 1459 & 1461). |
| `"What is your baggage allowance policy for economy passengers?"` | Policy RAG | Semantic vector retrieval over `policies.md` answering baggage limits. |
| `"Reschedule my ticket 7240005432906569 to upcoming flight 1461"` | Direct Mutation | Executes `update_ticket_to_new_flight` directly without pausing for approval. |
| `"Book car rental 2 (Avis Executive in Basel) for my trip"` | Direct Booking | Reserves available vehicle 2 directly in PostgreSQL without interruption. |
| `"Book Grand Hotel Les Trois Rois (hotel 1 in Basel)"` | Direct Booking | Confirms luxury hotel booking in database in a single autonomous turn. |

---

### 2. Part 2: Full Confirmation / Maximum Strictness (`part2`)
Designed to demonstrate graph interruption (`interrupt_before=["tools"]`) halting before **every single tool**, even read-only operations:

| Preset Input Option | Category | Expected Behavior & Assertion |
| :--- | :--- | :--- |
| `"Check my upcoming flight reservations"` | Read Pause | Graph halts before `fetch_user_flight_information`; asks permission to read tickets! |
| `"Look up the airline ticket cancellation and refund policy"` | Policy Pause | Graph halts before `lookup_policy`; asks permission to access policy documents! |
| `"Search for available flights from Basel to Paris"` | Search Pause | Graph halts before `search_flights`; asks permission to query schedule catalog! |
| `"Search for available rental cars in Basel"` | Catalog Pause | Graph halts before `search_car_rentals`; requires approval to read car list! |
| `"Find partner hotels in Basel"` | Catalog Pause | Graph halts before `search_hotels`; requires approval to read hotels table! |
| `"Rebook my ticket 7240005432906569 to flight 1461"` | Sensitive Pause | Graph halts before `update_ticket_to_new_flight`; requires approval to modify ticket! |

---

### 3. Part 3: Conditional Interrupt / Balanced HITL (`part3`)
Designed to demonstrate intelligent bifurcation: safe read-only tools run automatically, while sensitive actions pause for authorization:

| Preset Input Option | Category | Expected Behavior & Assertion |
| :--- | :--- | :--- |
| `"What flights do I have booked right now?"` | Safe Auto-Run | **Runs immediately with zero human delay.** Reads tickets and answers instantly. |
| `"Can I take a carry-on and personal item on my flight?"` | Safe Auto-Run | **Runs immediately with zero human delay.** Semantic policy RAG lookup. |
| `"Search available flights from Basel (BSL) to Paris (CDG)"` | Safe Auto-Run | **Runs immediately with zero human delay.** Returns flights 1459 and 1461. |
| `"Search for available rental cars in Basel"` | Safe Auto-Run | **Runs immediately with zero human delay.** Returns Avis Executive and National Car. |
| `"Please reschedule my ticket 7240005432906569 to flight 1461"` | Sensitive HITL | Safe verification auto-runs; ticket update **PAUSES** and renders approval card! |
| `"Book Grand Hotel Les Trois Rois (hotel 1 in Basel)"` | Sensitive HITL | Safe search auto-runs; hotel booking **PAUSES** for passenger confirmation. |
| `"Book car rental 2 (Avis Executive in Basel)"` | Sensitive HITL | Safe fleet search auto-runs; vehicle booking **PAUSES** for passenger confirmation. |

---

### 4. Part 4: Specialized Multi-Agent Swarm (`part4`)
Designed to demonstrate hierarchical routing from the Primary Concierge to 4 specialized domain agents, as well as dialog stack manipulation:

| Preset Input Option | Target Agent | Expected Behavior & Assertion |
| :--- | :--- | :--- |
| `"I need to speak to the flight updates desk to check my flight status"` | Flight Specialist (`update_flight`) | Primary calls `ToFlightBookingAssistant`; enters `update_flight` workflow. |
| `"Connect me to the car rental specialist to find available cars in Basel"` | Car Specialist (`book_car_rental`) | Primary calls `ToBookCarRental`; enters `book_car_rental` workflow. |
| `"Transfer me to the hotel concierge to search luxury hotels in Basel"` | Hotel Specialist (`book_hotel`) | Primary calls `ToHotelBookingAssistant`; enters `book_hotel` workflow. |
| `"Connect me to the excursion guide for scenic tours in Basel"` | Excursion Specialist (`book_excursion`) | Primary calls `ToBookExcursion`; enters `book_excursion` workflow. |
| `"What are your customer support policies regarding baggage allowances?"` | Primary Concierge | Primary answers directly with `lookup_policy` without delegating to specialists. |
| `"I am finished with car rentals, please return to the main concierge"` | Concierge Escalate (`leave_skill`) | Specialist calls `CompleteOrEscalate`; pops dialog stack and returns to Primary. |


