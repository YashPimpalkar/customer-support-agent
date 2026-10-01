# 🏛️ AeroAssist System Architecture (`architecher.md`)

This architectural document provides an in-depth blueprint of the **AeroAssist** enterprise airline customer support system. It details the multi-agent graph mechanics, state management, Human-in-the-Loop (HITL) interrupt pipelines, PostgreSQL relational data layer, RAG knowledge retrieval, and React frontend integration.

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer["🖥️ Frontend Client (Vite + React 19 + TailwindCSS v4)"]
        UI["Passenger UI & Concierge Console"]
        ApprovalCard["HITL Approval Card (Approve / Deny)"]
        ItineraryBoard["Live Boarding Passes & Catalog View"]
    end

    subgraph APILayer["⚡ Backend REST Gateway (FastAPI + Uvicorn)"]
        Router["/api/chat & /api/chat/approve"]
        HealthEndpoint["/api/health & /api/database/stats"]
        PassengerEndpoints["/api/passengers & /api/flights"]
    end

    subgraph AgentLayer["🧠 LangGraph Orchestration Engine"]
        AgentMgr["AgentManager (Session & Checkpoint Controller)"]
        Checkpointer[("MemorySaver Checkpointer (thread_id)")]
        Part1["Part 1: Zero-Shot Graph"]
        Part2["Part 2: Full Confirmation Graph"]
        Part3["Part 3: Conditional Interrupt Graph"]
        Part4["Part 4: Specialized Multi-Agent Swarm"]
    end

    subgraph ModelLayer["🤖 LLM & Vector Embeddings"]
        GeminiChat["Google Gemini 3.8 Flash (ChatGoogleGenerativeAI)"]
        GeminiEmbed["Google text-embedding-004 (GoogleGenerativeAIEmbeddings)"]
    end

    subgraph DataLayer["🗄️ Persistence & Knowledge Layer"]
        NeonDB[("Neon PostgreSQL Cloud Database")]
        PolicyDoc["Airline Policies Knowledge Base (Markdown)"]
        VectorIndex["In-Memory Cosine Similarity Matrix"]
    end

    UI -->|"HTTP POST /api/chat"| Router
    ApprovalCard -->|"HTTP POST /api/chat/approve"| Router
    ItineraryBoard -->|"HTTP GET /api/passengers/:id/overview"| PassengerEndpoints

    Router --> AgentMgr
    AgentMgr <--> Checkpointer
    AgentMgr --> Part1 & Part2 & Part3 & Part4

    Part1 & Part2 & Part3 & Part4 <--> GeminiChat
    Part1 & Part2 & Part3 & Part4 --> NeonDB
    Part1 & Part2 & Part3 & Part4 --> VectorIndex

    PolicyDoc --> GeminiEmbed --> VectorIndex
```

---

## 2. Multi-Tier LangGraph Agent Architectures

AeroAssist incorporates 4 distinct customer support architectures compiled with **LangGraph**:

### Part 1: Zero-Shot Agent (Unconstrained Direct Execution)
In Part 1, all tools (both safe queries and sensitive mutations) execute immediately upon model invocation.
```mermaid
flowchart LR
    S([START]) --> Fetch[fetch_user_info]
    Fetch --> Assistant[Assistant]
    Assistant --> Condition{tools_condition}
    Condition -->|tools| Tools[ToolNode: All 14 Tools]
    Condition -->|no tools| E([END])
    Tools --> Assistant
```

---

### Part 2: Full Confirmation Agent (Every Tool Pauses)
In Part 2, the graph defines `interrupt_before=["tools"]`. The system halts before executing *any* tool (even read-only searches), requiring explicit human confirmation.
```mermaid
flowchart LR
    S([START]) --> Fetch[fetch_user_info]
    Fetch --> Assistant[Assistant]
    Assistant --> Condition{tools_condition}
    Condition -->|requires tools| Pause[⏸️ INTERRUPT before tools]
    Pause -->|approved| Tools[ToolNode: All 14 Tools]
    Condition -->|no tools| E([END])
    Tools --> Assistant
```

---

### Part 3: Conditional Interrupt Agent (Safe vs Sensitive Bifurcation)
Part 3 dynamically inspects the proposed tool calls. Read-only search and lookup tools execute in real time without human latency, while sensitive write operations pause at graph interrupts.
```mermaid
flowchart TD
    S([START]) --> Fetch[fetch_user_info]
    Fetch --> Assistant[Assistant]
    Assistant --> Router{_route_part3_tools}
    Router -->|Safe Tools| SafeNode[ToolNode: SAFE_TOOLS]
    Router -->|Sensitive Tools| Pause[⏸️ INTERRUPT before sensitive_tools]
    Router -->|No Tools| E([END])
    Pause -->|Passenger Approval| SensitiveNode[ToolNode: SENSITIVE_TOOLS]
    SafeNode --> Assistant
    SensitiveNode --> Assistant
```

---

### Part 4: Specialized Multi-Agent Swarm (Hierarchical Delegation)
Part 4 is the pinnacle enterprise multi-agent architecture. It organizes domain tasks into specialized mini-agents governed by a central **Primary Assistant** router with a dynamic dialog stack.

```mermaid
flowchart TD
    S([START]) --> Fetch[fetch_user_info]
    Fetch --> RouteInit{_route_to_workflow}
    RouteInit -->|dialog_state empty| Primary[primary_assistant]
    RouteInit -->|update_flight in stack| Flight[update_flight]
    RouteInit -->|book_car_rental in stack| Car[book_car_rental]
    RouteInit -->|book_hotel in stack| Hotel[book_hotel]
    RouteInit -->|book_excursion in stack| Excursion[book_excursion]

    %% Primary routing
    Primary --> RoutePrimary{_route_primary_assistant}
    RoutePrimary -->|ToFlightBookingAssistant| EnterFlight[enter_update_flight]
    RoutePrimary -->|ToBookCarRental| EnterCar[enter_book_car_rental]
    RoutePrimary -->|ToHotelBookingAssistant| EnterHotel[enter_book_hotel]
    RoutePrimary -->|ToBookExcursion| EnterExcursion[enter_book_excursion]
    RoutePrimary -->|primary tools| PrimaryTools[primary_assistant_tools]
    RoutePrimary -->|direct text| E([END])
    PrimaryTools --> Primary

    EnterFlight --> Flight
    EnterCar --> Car
    EnterHotel --> Hotel
    EnterExcursion --> Excursion

    %% Flight specialist
    Flight --> RouteFlight{Flight Router}
    RouteFlight -->|Safe| FlightSafe[update_flight_safe_tools]
    RouteFlight -->|Sensitive| FlightPause[⏸️ INTERRUPT: Flight Sensitive]
    FlightPause -->|Approved| FlightSens[update_flight_sensitive_tools]
    RouteFlight -->|CompleteOrEscalate| LeaveSkill[leave_skill: pop stack]
    FlightSafe --> Flight
    FlightSens --> Flight

    %% Car specialist
    Car --> RouteCar{Car Router}
    RouteCar -->|Safe| CarSafe[book_car_rental_safe_tools]
    RouteCar -->|Sensitive| CarPause[⏸️ INTERRUPT: Car Sensitive]
    CarPause -->|Approved| CarSens[book_car_rental_sensitive_tools]
    RouteCar -->|CompleteOrEscalate| LeaveSkill
    CarSafe --> Car
    CarSens --> Car

    %% Hotel specialist
    Hotel --> RouteHotel{Hotel Router}
    RouteHotel -->|Safe| HotelSafe[book_hotel_safe_tools]
    RouteHotel -->|Sensitive| HotelPause[⏸️ INTERRUPT: Hotel Sensitive]
    HotelPause -->|Approved| HotelSens[book_hotel_sensitive_tools]
    RouteHotel -->|CompleteOrEscalate| LeaveSkill
    HotelSafe --> Hotel
    HotelSens --> Hotel

    %% Excursion specialist
    Excursion --> RouteExcursion{Excursion Router}
    RouteExcursion -->|Safe| ExcursionSafe[book_excursion_safe_tools]
    RouteExcursion -->|Sensitive| ExcursionPause[⏸️ INTERRUPT: Excursion Sensitive]
    ExcursionPause -->|Approved| ExcursionSens[book_excursion_sensitive_tools]
    RouteExcursion -->|CompleteOrEscalate| LeaveSkill
    ExcursionSafe --> Excursion
    ExcursionSens --> Excursion

    LeaveSkill --> Primary
```

---

## 3. Human-in-the-Loop (HITL) Execution Engine

### Interruption Triggering
When the graph encounters an interrupt-configured node:
1. `graph.stream(..., stream_mode="values")` yields messages up to the AI's tool call.
2. The runtime freezes execution immediately prior to running the sensitive node.
3. `graph.get_state(cfg).next` holds the name of the pending node (e.g. `['update_flight_sensitive_tools']`).
4. `AgentManager._format_agent_output()` extracts the proposed tool call and arguments, generates a unique `action_id`, and stores an entry in the `pending_actions` table.
5. The API response returns `{"status": "requires_approval", "action_id": "...", "actions": [...]}`.

### Resumption via Passenger Approval
When the passenger clicks **Approve**:
```python
# graph.stream with None input continues from current checkpoint
events = list(graph.stream(None, cfg, stream_mode="values"))
DatabaseService.update_pending_action_status(action_id, "approved")
```

### Resumption via Passenger Denial
When the passenger clicks **Deny**:
```python
# Inject synthetic ToolMessage into the frozen tool node
graph.update_state(
    cfg,
    {
        "messages": [
            ToolMessage(
                tool_call_id=tc["id"],
                content=f"Action denied by passenger. Reason: '{denial_reason}'. Continue assisting.",
            )
            for tc in last_ai.tool_calls
        ]
    },
    as_node=pending_node,
)
DatabaseService.update_pending_action_status(action_id, "denied")
# Resume graph execution so the agent can propose alternative options
events = list(graph.stream(None, cfg, stream_mode="values"))
```

---

## 4. Neon PostgreSQL Relational Schema

```
                               ┌───────────────────┐
                               │   airports_data   │
                               ├───────────────────┤
                               │ airport_code (PK) │
                               │ airport_name      │
                               │ city, timezone    │
                               └─────────┬─────────┘
                                         │
                                         ▼
┌───────────────────┐          ┌───────────────────┐
│  aircrafts_data   │          │      flights      │
├───────────────────┤          ├───────────────────┤
│ aircraft_code(PK) │◄─────────┤ flight_id (PK)    │
│ model, range      │          │ departure_airport │
└───────────────────┘          │ arrival_airport   │
                               │ scheduled_dep/arr │
                               └─────────┬─────────┘
                                         │
                                         ▼
┌───────────────────┐          ┌───────────────────┐
│     bookings      │          │  ticket_flights   │
├───────────────────┤          ├───────────────────┤
│ book_ref (PK)     │◄─────────┤ ticket_no (FK)    │
│ book_date, total  │          │ flight_id (FK)    │
└─────────┬─────────┘          │ fare_conditions   │
          │                    └─────────┬─────────┘
          ▼                              │
┌───────────────────┐                    ▼
│      tickets      │          ┌───────────────────┐
├───────────────────┤          │  boarding_passes  │
│ ticket_no (PK)    │◄─────────┤ ticket_no (FK)    │
│ passenger_id      │          │ flight_id (FK)    │
│ passenger_name    │          │ seat_no, boarding │
└───────────────────┘          └───────────────────┘

┌───────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
│    car_rentals    │ │      hotels       │ │  trip_recommendations  │
├───────────────────┤ ├───────────────────┤ ├────────────────────────┤
│ rental_id (PK)    │ │ hotel_id (PK)     │ │ recommendation_id (PK) │
│ company, location │ │ name, location    │ │ title, location        │
│ booked, passenger │ │ booked, passenger │ │ booked, passenger_id   │
└───────────────────┘ └───────────────────┘ └────────────────────────┘
```

---

## 5. Policy Knowledge Base (RAG) Architecture

1. **Document Ingestion**:
   - `backend/app/rag/policies.md` contains markdown sections detailing flight cancellations, baggage limits, flight change policies, car rental terms, and hotel policies.
2. **Embedding & Cosine Retrieval**:
   - `PolicyRetriever` uses `GoogleGenerativeAIEmbeddings(model="text-embedding-004")` to generate 768-dimensional vectors.
   - Vectors are normalized into a unit matrix: $\hat{v} = v / \|v\|$.
   - Search query $q$ is embedded and projected: $\text{scores} = M \cdot \hat{q}$.
3. **Keyword Fallback**:
   - If the API key is not supplied or offline, the retriever transparently falls back to token overlap scoring: $\frac{|W_q \cap W_c|}{\max(|W_q|, 1)}$.

---

## 6. Directory Layout & Organization

```
customer_support_app/
├── main.py                     # Root ASGI & CLI launcher
├── README.md                   # Fullstack project documentation
├── agents.md                   # Detailed agent specifications & safety matrix
├── architecher.md              # Complete system architecture specification
├── .gitignore                  # Git ignore rules
│
├── backend/                    # Python Backend
│   ├── run.py                  # Direct runner script
│   ├── requirements.txt        # Backend dependencies
│   ├── __init__.py             # Clean top-level package exports
│   ├── app/
│   │   ├── main.py             # FastAPI application instance & CORS
│   │   ├── routes.py           # REST endpoints
│   │   ├── config.py           # Settings, DB URLs, Gemini factory
│   │   ├── db.py               # DatabaseService & connection pooler
│   │   ├── agents/
│   │   │   ├── graph.py        # LangGraph StateGraphs (Parts 1 - 4)
│   │   │   ├── manager.py      # Session orchestrator & approval handler
│   │   │   ├── prompts.py      # System prompts for all agents
│   │   │   ├── tools.py        # 14 LangChain database tools
│   │   │   └── delegation.py   # Pydantic delegation schemas
│   │   ├── rag/
│   │   │   ├── retriever.py    # PolicyRetriever & vector similarity
│   │   │   └── policies.md     # Airline policies markdown knowledge base
│   │   └── scripts/
│   │       └── seed.py         # Schema migration & sample data populator
│   └── tests/
│       └── test_backend.py     # 14 Unit and integration test cases
│
└── frontend/                   # React 19 Frontend
    ├── index.html              # HTML5 entrypoint
    ├── vite.config.ts          # Vite build & backend proxy (/api -> :5000)
    ├── package.json            # Node dependencies
    └── src/
        ├── App.tsx             # Root dual-column layout
        ├── api.ts              # Typed backend API client
        ├── types.ts            # Data models & interfaces
        ├── index.css           # TailwindCSS v4 theme tokens
        └── components/
            ├── Navbar.tsx          # Passenger selector & agent mode picker
            ├── ChatPanel.tsx       # Message thread & approval action cards
            ├── DashboardPanel.tsx  # Boarding passes & active bookings
            └── DatabaseModal.tsx   # Neon DB inspector & re-seeder
```

---

## 7. Mode-Specific Input Architecture & User Interaction Options

To evaluate the operational differences across the 4 LangGraph architectures, the UI and API dynamically adapt the input options and starter presets:

```mermaid
graph TD
    ModeSelect[User Selects Agent Mode in Navbar] --> ModeChange{Mode Switcher}
    
    ModeChange -->|part1: Zero-Shot| P1UI[Part 1 Input Options: Immediate direct execution, no pauses]
    ModeChange -->|part2: Full Confirmation| P2UI[Part 2 Input Options: Read/Write queries pause for approval]
    ModeChange -->|part3: Conditional Interrupt| P3UI[Part 3 Input Options: Safe auto-runs, Sensitive pauses]
    ModeChange -->|part4: Specialized Swarm| P4UI[Part 4 Input Options: Departmental hand-off & stack pop]

    P1UI --> ChatStream[Chat Stream & Interactive Execution]
    P2UI --> ChatStream
    P3UI --> ChatStream
    P4UI --> ChatStream
```

| Mode ID | Architecture Type | Input Categories | Purpose in Demonstrating System |
| :--- | :--- | :--- | :--- |
| `part1` | Zero-Shot Agent | `[Instant Read]`, `[Direct Ticket Change]`, `[Policy RAG]`, `[Direct Booking]` | Demonstrates unconstrained execution where even ticket changes commit without pausing. |
| `part2` | Full Confirmation Agent | `[Read Query Pauses]`, `[Policy Read Pauses]`, `[Search Pauses]`, `[Sensitive Mod Pauses]` | Demonstrates total human oversight where the graph halts before reading or writing data. |
| `part3` | Conditional Interrupt | `[Safe Read (Auto)]`, `[Safe Policy (Auto)]`, `[Sensitive Re-book (HITL)]`, `[Sensitive Cancel (HITL)]` | Demonstrates optimal production balance: read queries run instantly; financial/ticket writes pause for authorization. |
| `part4` | Specialized Multi-Agent Swarm | `[Flight Specialist]`, `[Car Specialist]`, `[Hotel Specialist]`, `[Excursion Specialist]`, `[Escalate / Pop Stack]` | Demonstrates intent routing across domain specialists and bidirectional dialog stack transitions. |

