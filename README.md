# ✈️ AeroAssist | Enterprise Airline Customer Support AI

Enterprise airline customer support application powered by **LangGraph**, **Google Gemini (Gemini 3.8 Flash)**, and **Neon PostgreSQL**, featuring **Human-in-the-Loop (HITL)** sensitive action authorization and a modern **React 19 + TailwindCSS v4** dashboard.

---

## 🌟 Highlights

- **4 LangGraph Agent Architectures**:
  - **Part 1 (Zero-Shot)**: Direct tool execution without interruptions.
  - **Part 2 (Full Confirmation)**: Pauses before every tool call for human confirmation.
  - **Part 3 (Conditional Interrupt)**: Safe tools (read-only queries, policy search) execute automatically; sensitive operations (ticket changes, cancellations, bookings) pause for passenger authorization.
  - **Part 4 (Specialized Swarm)**: Primary assistant router orchestrates 4 specialized domain agents (Flight Updates, Car Rentals, Hotel Bookings, Excursions) using a dynamic dialog stack.
- **Human-in-the-Loop (HITL)**:
  - When sensitive actions are triggered, execution halts at graph interrupts.
  - Interactive authorization cards appear directly in the passenger chat with full parameter summaries and **Approve** / **Deny** buttons.
- **Neon PostgreSQL Integration**:
  - Live relational database populated with 115 international airports, 115 flights, 9 aircraft types, bookings, tickets, boarding passes, car rentals, hotels, and excursions.
  - Live table metrics and database reseeder built right into the UI.
- **RAG Policy Knowledge Base**:
  - Embeddings-based policy retrieval (`text-embedding-004`) with keyword search fallback for rapid baggage and cancellation policy lookup.
- **Clean Architecture & Folder Structure**:
  - Modular backend package (`backend/app/agents`, `backend/app/rag`, `backend/app/scripts`).
  - Comprehensive documentation in [`agents.md`](file:///home/client/langraph/customer_support_app/agents.md) and [`architecher.md`](file:///home/client/langraph/customer_support_app/architecher.md).

---

## 📁 Project Structure

```
customer_support_app/
├── main.py                     # Root ASGI & CLI launcher
├── README.md                   # Project overview & quickstart
├── agents.md                   # Agent specifications & tool safety matrix
├── architecher.md              # Full system architecture & Mermaid diagrams
│
├── backend/                    # Python Backend
│   ├── run.py                  # Backend launcher script
│   ├── requirements.txt        # Python dependencies
│   ├── __init__.py             # Clean top-level package exports
│   ├── app/
│   │   ├── main.py             # FastAPI instance & CORS middleware
│   │   ├── routes.py           # REST endpoints
│   │   ├── config.py           # Environment variables & LLM factory
│   │   ├── db.py               # DatabaseService & connection management
│   │   ├── agents/
│   │   │   ├── graph.py        # 4 LangGraph StateGraph architectures
│   │   │   ├── manager.py      # Session orchestrator & approval handler
│   │   │   ├── prompts.py      # System prompts for all agents
│   │   │   ├── tools.py        # 14 LangChain database tools
│   │   │   └── delegation.py   # Pydantic delegation transfer schemas
│   │   ├── rag/
│   │   │   ├── retriever.py    # PolicyRetriever & cosine similarity
│   │   │   └── policies.md     # Airline policies knowledge base
│   │   └── scripts/
│   │       └── seed.py         # Database schema & sample data seeder
│   └── tests/
│       └── test_backend.py     # 14 Unit & integration test cases
│
└── frontend/                   # React 19 Frontend
    ├── index.html              # HTML5 entrypoint
    ├── vite.config.ts          # Vite build & backend API proxy
    ├── package.json            # Node dependencies
    └── src/
        ├── App.tsx             # Root layout with 2-column chat & dashboard
        ├── api.ts              # Typed API client
        ├── types.ts            # TypeScript interfaces
        ├── index.css           # TailwindCSS v4 theme tokens
        └── components/
            ├── Navbar.tsx          # Passenger selector & agent mode switcher
            ├── ChatPanel.tsx       # Message thread & approval action cards
            ├── DashboardPanel.tsx  # Boarding passes & active bookings
            └── DatabaseModal.tsx   # Neon DB live explorer & reseeder
```

---

## 🚀 Running the Application

### 1. Run Backend Server

You can launch the backend from the project root using either:

```bash
cd customer_support_app
.venv/bin/python main.py
```
*Or using uvicorn:*
```bash
.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 5000 --reload
```
*Backend API runs on `http://127.0.0.1:5000` with Swagger docs at `http://127.0.0.1:5000/docs`.*

---

### 2. Run Frontend Server

In a separate terminal:

```bash
cd customer_support_app/frontend
npm run dev
```
*Frontend runs on `http://localhost:5173` (proxies `/api` requests to backend on port 5000).*

---

### 3. Run Test Suite

```bash
cd customer_support_app
.venv/bin/python -m unittest backend.tests.test_backend
```

All 14 unit and integration tests validate the database access layer, policy RAG retriever, and FastAPI endpoints.

---

## 📚 Architectural & Agent Documentation

- **[`agents.md`](file:///home/client/langraph/customer_support_app/agents.md)**: Full agent catalog, primary assistant routing, specialist agent definitions, tool safety classifications, and escalation mechanisms.
- **[`architecher.md`](file:///home/client/langraph/customer_support_app/architecher.md)**: End-to-end system architecture, Mermaid state diagrams for all 4 LangGraph architectures, HITL interruption lifecycle, and database ERD.
