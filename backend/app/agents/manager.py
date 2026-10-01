"""Agent Manager: Orchestrates chat sessions, graph execution, and Human-in-the-Loop approval."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from .graph import GRAPHS
from ..db import DatabaseService


def _stream_with_retry(graph, input_data, cfg, max_attempts=3):
    import time
    for attempt in range(max_attempts):
        try:
            return list(graph.stream(input_data, cfg, stream_mode="values"))
        except Exception as e:
            err_text = str(e).lower()
            if any(k in err_text for k in ["503", "unavailable", "429", "resource_exhausted", "high demand"]) and attempt < max_attempts - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise


class AgentManager:
    """Manages chat sessions, graph invocations, and pending approvals across all 4 architectures."""

    @staticmethod
    def get_graph(mode: str = "part3"):
        """Retrieve the compiled graph instance for the requested mode."""
        return GRAPHS.get(mode.lower(), GRAPHS["part3"])

    @staticmethod
    def process_message(
        passenger_id: str,
        thread_id: str,
        user_message: str,
        mode: str = "part3",
    ) -> Dict[str, Any]:
        """Send a user message to the chosen LangGraph architecture."""
        graph = AgentManager.get_graph(mode)
        cfg = {"configurable": {"passenger_id": passenger_id, "thread_id": thread_id}}

        # Stream until end of turn or interrupt with automatic retry on temporary high demand / 503
        events = _stream_with_retry(
            graph,
            {"messages": [HumanMessage(content=user_message)]},
            cfg,
        )

        snapshot = graph.get_state(cfg)
        return AgentManager._format_agent_output(snapshot, thread_id, passenger_id, mode)

    @staticmethod
    def resolve_action(
        passenger_id: str,
        thread_id: str,
        action_id: str,
        approved: bool,
        reason: Optional[str] = None,
        mode: str = "part3",
    ) -> Dict[str, Any]:
        """Resume graph execution following approval or denial of pending tool call."""
        graph = AgentManager.get_graph(mode)
        cfg = {"configurable": {"passenger_id": passenger_id, "thread_id": thread_id}}
        snapshot = graph.get_state(cfg)

        if not snapshot.next:
            return {
                "status": "completed",
                "message": "No action was pending for this session.",
                "tool_calls": [],
                "mode": mode,
            }

        pending_node = snapshot.next[0]
        last_ai = snapshot.values["messages"][-1]

        if approved:
            events = _stream_with_retry(graph, None, cfg)
            DatabaseService.update_pending_action_status(action_id, "approved")
        else:
            denial_reason = reason or "Passenger declined this action."
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
            events = _stream_with_retry(graph, None, cfg)

        new_snapshot = graph.get_state(cfg)
        return AgentManager._format_agent_output(new_snapshot, thread_id, passenger_id, mode)

    @staticmethod
    def _format_agent_output(
        snapshot: Any,
        thread_id: str,
        passenger_id: str,
        mode: str = "part3",
    ) -> Dict[str, Any]:
        messages = snapshot.values.get("messages", [])
        if not messages:
            return {
                "status": "completed",
                "message": "Ready to assist.",
                "tool_calls": [],
                "mode": mode,
            }

        # Check if paused before any interruptible node
        if snapshot.next:
            last_ai = messages[-1]
            pending_calls = getattr(last_ai, "tool_calls", [])
            action_id = str(uuid.uuid4())

            formatted_actions = []
            for tc in pending_calls:
                name = tc.get("name", "unknown")
                args = tc.get("args", {})
                description = AgentManager._describe_tool_call(name, args)
                formatted_actions.append({
                    "name": name,
                    "args": args,
                    "description": description,
                })
                DatabaseService.create_pending_action(
                    action_id=action_id,
                    session_id=thread_id,
                    tool_name=name,
                    tool_args=args,
                    description=description,
                )

            return {
                "status": "requires_approval",
                "action_id": action_id,
                "thread_id": thread_id,
                "mode": mode,
                "actions": formatted_actions,
                "message": (
                    last_ai.content
                    if isinstance(last_ai.content, str) and last_ai.content
                    else "I need your confirmation before performing this action:"
                ),
            }

        # Completed turn
        last_msg = messages[-1]
        text_content = ""
        if isinstance(last_msg.content, str):
            text_content = last_msg.content
        elif isinstance(last_msg.content, list):
            text_content = "\n".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in last_msg.content
            )

        executed_tools = []
        for msg in messages[-6:]:
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    executed_tools.append(tc.get("name"))

        return {
            "status": "completed",
            "message": text_content or "Action completed.",
            "tool_calls": list(set(executed_tools)),
            "mode": mode,
        }

    @staticmethod
    def _describe_tool_call(name: str, args: Dict[str, Any]) -> str:
        if name == "update_ticket_to_new_flight":
            return f"Re-book Ticket #{args.get('ticket_no')} onto Flight #{args.get('new_flight_id')}"
        if name == "cancel_ticket":
            return f"Cancel Flight Ticket #{args.get('ticket_no')}"
        if name == "book_car_rental":
            return f"Confirm reservation for Car Rental #{args.get('rental_id')}"
        if name == "cancel_car_rental":
            return f"Cancel Car Rental #{args.get('rental_id')}"
        if name == "book_hotel":
            return f"Confirm booking for Hotel #{args.get('hotel_id')}"
        if name == "cancel_hotel":
            return f"Cancel reservation for Hotel #{args.get('hotel_id')}"
        if name == "book_excursion":
            return f"Confirm ticket for Excursion Activity #{args.get('recommendation_id')}"
        if name == "cancel_excursion":
            return f"Cancel Excursion #{args.get('recommendation_id')}"
        if name == "search_flights":
            return f"Search flights: {args}"
        if name == "lookup_policy":
            return f"Lookup airline policy: '{args.get('query')}'"
        return f"Run action: {name} with parameters {args}"
