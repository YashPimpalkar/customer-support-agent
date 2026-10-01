"""LangGraph compilation definitions for all 4 customer support architectures:

- Part 1: Zero-shot agent (direct tool execution, no approval required)
- Part 2: Add confirmation (pauses before every tool call for human approval)
- Part 3: Conditional interrupt (safe tools run automatically, sensitive tools pause)
- Part 4: Specialized workflows (primary assistant router + 4 domain specialists)
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from .. import config
from . import tools
from .delegation import (
    CompleteOrEscalate,
    ToBookCarRental,
    ToBookExcursion,
    ToFlightBookingAssistant,
    ToHotelBookingAssistant,
)
from .prompts import (
    SYSTEM_PROMPT,
    build_car_rental_prompt,
    build_excursion_prompt,
    build_flight_prompt,
    build_hotel_prompt,
    build_primary_prompt,
)

# ---------------------------------------------------------------------------
# State & Helpers
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str


def update_dialog_stack(left: list[str], right: str | None) -> list[str]:
    """Manages the dialog state stack for multi-agent delegation."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class Part4State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[list[str], update_dialog_stack]


class AssistantWrapper:
    """Wraps the runnable model, re-prompting if the output is empty."""

    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: Dict[str, Any], config: RunnableConfig = None):
        while True:
            result = self.runnable.invoke(state, config=config)
            no_tool_calls = not getattr(result, "tool_calls", None)
            empty_text = False
            if not result.content:
                empty_text = True
            elif isinstance(result.content, list):
                if len(result.content) == 0:
                    empty_text = True
                elif isinstance(result.content[0], dict) and not result.content[0].get("text"):
                    empty_text = True
                elif isinstance(result.content[0], str) and not result.content[0].strip():
                    empty_text = True
            elif isinstance(result.content, str) and not result.content.strip():
                empty_text = True

            if no_tool_calls and empty_text:
                state = {
                    **state,
                    "messages": state["messages"]
                    + [HumanMessage(content="Please provide a clear and helpful response.")],
                }
                continue
            break
        return {"messages": result}


def handle_tool_error(state: dict) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error executing action: {error!r}\nPlease adjust parameters and try again.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tool_list: list) -> Runnable:
    return ToolNode(tool_list).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _get_base_prompt():
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )


def _user_info_node(state: Dict[str, Any], config: RunnableConfig = None):
    cfg = config or {}
    info = tools.fetch_user_flight_information.invoke({}, config=cfg)
    return {"user_info": str(info)}


# Shared checkpointer
CHECKPOINTER = MemorySaver()


# ---------------------------------------------------------------------------
# 1. Part 1 Graph - Zero-shot Agent (No Confirmation)
# ---------------------------------------------------------------------------


def build_part1_graph():
    llm = config.get_llm(temperature=0.3)
    assistant_runnable = _get_base_prompt() | llm.bind_tools(tools.ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("fetch_user_info", _user_info_node)
    graph.add_node("assistant", AssistantWrapper(assistant_runnable))
    graph.add_node("tools", create_tool_node_with_fallback(tools.ALL_TOOLS))

    graph.add_edge(START, "fetch_user_info")
    graph.add_edge("fetch_user_info", "assistant")
    graph.add_conditional_edges("assistant", tools_condition)
    graph.add_edge("tools", "assistant")

    return graph.compile(checkpointer=CHECKPOINTER)


# ---------------------------------------------------------------------------
# 2. Part 2 Graph - Full Confirmation (Pauses Before Every Tool)
# ---------------------------------------------------------------------------


def build_part2_graph():
    llm = config.get_llm(temperature=0.3)
    assistant_runnable = _get_base_prompt() | llm.bind_tools(tools.ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("fetch_user_info", _user_info_node)
    graph.add_node("assistant", AssistantWrapper(assistant_runnable))
    graph.add_node("tools", create_tool_node_with_fallback(tools.ALL_TOOLS))

    graph.add_edge(START, "fetch_user_info")
    graph.add_edge("fetch_user_info", "assistant")
    graph.add_conditional_edges("assistant", tools_condition)
    graph.add_edge("tools", "assistant")

    # Pauses before ANY tool runs
    return graph.compile(checkpointer=CHECKPOINTER, interrupt_before=["tools"])


# ---------------------------------------------------------------------------
# 3. Part 3 Graph - Conditional Interrupt (Sensitive Tools Only)
# ---------------------------------------------------------------------------


def _route_part3_tools(state: AgentState):
    next_node = tools_condition(state)
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    sensitive_names = {t.name for t in tools.SENSITIVE_TOOLS}
    if any(tc["name"] in sensitive_names for tc in ai_message.tool_calls):
        return "sensitive_tools"
    return "safe_tools"


def build_part3_graph():
    llm = config.get_llm(temperature=0.3)
    assistant_runnable = _get_base_prompt() | llm.bind_tools(tools.ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("fetch_user_info", _user_info_node)
    graph.add_node("assistant", AssistantWrapper(assistant_runnable))
    graph.add_node("safe_tools", create_tool_node_with_fallback(tools.SAFE_TOOLS))
    graph.add_node("sensitive_tools", create_tool_node_with_fallback(tools.SENSITIVE_TOOLS))

    graph.add_edge(START, "fetch_user_info")
    graph.add_edge("fetch_user_info", "assistant")
    graph.add_conditional_edges(
        "assistant",
        _route_part3_tools,
        {"safe_tools": "safe_tools", "sensitive_tools": "sensitive_tools", END: END},
    )
    graph.add_edge("safe_tools", "assistant")
    graph.add_edge("sensitive_tools", "assistant")

    return graph.compile(
        checkpointer=CHECKPOINTER,
        interrupt_before=["sensitive_tools"],
    )


# ---------------------------------------------------------------------------
# 4. Part 4 Graph - Specialized Workflows (Multi-Agent Swarm)
# ---------------------------------------------------------------------------


def create_entry_node(assistant_name: str, new_dialog_state: str):
    def entry_node(state: Part4State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=(
                        f"The assistant is now the {assistant_name}. Assist the customer. "
                        "If the customer changes their mind or asks about something outside your domain, "
                        "call CompleteOrEscalate to hand control back to the primary assistant."
                    ),
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node


def pop_dialog_state(state: Part4State) -> dict:
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with the primary assistant.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {"dialog_state": "pop", "messages": messages}


def _make_specialist_router(
    safe_names: set[str],
    sensitive_names: set[str],
    safe_node: str,
    sensitive_node: str,
):
    def router(state: Part4State):
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        if any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls):
            return "leave_skill"
        names = {tc["name"] for tc in tool_calls}
        if names & sensitive_names:
            return sensitive_node
        return safe_node

    return router


def _route_primary_assistant(state: Part4State):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        name = tool_calls[0]["name"]
        if name == ToFlightBookingAssistant.__name__:
            return "enter_update_flight"
        if name == ToBookCarRental.__name__:
            return "enter_book_car_rental"
        if name == ToHotelBookingAssistant.__name__:
            return "enter_book_hotel"
        if name == ToBookExcursion.__name__:
            return "enter_book_excursion"
        return "primary_assistant_tools"
    return END


def _route_to_workflow(state: Part4State) -> str:
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"
    return dialog_state[-1]


def build_part4_graph():
    llm = config.get_llm(temperature=0.3)

    flight_runnable = build_flight_prompt() | llm.bind_tools(
        tools.FLIGHT_SAFE_TOOLS + tools.FLIGHT_SENSITIVE_TOOLS + [CompleteOrEscalate]
    )
    car_rental_runnable = build_car_rental_prompt() | llm.bind_tools(
        tools.CAR_RENTAL_SAFE_TOOLS + tools.CAR_RENTAL_SENSITIVE_TOOLS + [CompleteOrEscalate]
    )
    hotel_runnable = build_hotel_prompt() | llm.bind_tools(
        tools.HOTEL_SAFE_TOOLS + tools.HOTEL_SENSITIVE_TOOLS + [CompleteOrEscalate]
    )
    excursion_runnable = build_excursion_prompt() | llm.bind_tools(
        tools.EXCURSION_SAFE_TOOLS + tools.EXCURSION_SENSITIVE_TOOLS + [CompleteOrEscalate]
    )
    primary_runnable = build_primary_prompt() | llm.bind_tools(
        tools.PRIMARY_ASSISTANT_TOOLS
        + [ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, ToBookExcursion]
    )

    graph = StateGraph(Part4State)
    graph.add_node("fetch_user_info", _user_info_node)
    graph.add_edge(START, "fetch_user_info")

    # Flights Specialist
    graph.add_node("enter_update_flight", create_entry_node("Flight Updates Specialist", "update_flight"))
    graph.add_node("update_flight", AssistantWrapper(flight_runnable))
    graph.add_edge("enter_update_flight", "update_flight")
    graph.add_node("update_flight_safe_tools", create_tool_node_with_fallback(tools.FLIGHT_SAFE_TOOLS))
    graph.add_node("update_flight_sensitive_tools", create_tool_node_with_fallback(tools.FLIGHT_SENSITIVE_TOOLS))
    graph.add_edge("update_flight_safe_tools", "update_flight")
    graph.add_edge("update_flight_sensitive_tools", "update_flight")
    graph.add_conditional_edges(
        "update_flight",
        _make_specialist_router(
            {t.name for t in tools.FLIGHT_SAFE_TOOLS},
            {t.name for t in tools.FLIGHT_SENSITIVE_TOOLS},
            "update_flight_safe_tools",
            "update_flight_sensitive_tools",
        ),
        ["update_flight_safe_tools", "update_flight_sensitive_tools", "leave_skill", END],
    )

    # Car Rentals Specialist
    graph.add_node("enter_book_car_rental", create_entry_node("Car Rental Specialist", "book_car_rental"))
    graph.add_node("book_car_rental", AssistantWrapper(car_rental_runnable))
    graph.add_edge("enter_book_car_rental", "book_car_rental")
    graph.add_node("book_car_rental_safe_tools", create_tool_node_with_fallback(tools.CAR_RENTAL_SAFE_TOOLS))
    graph.add_node("book_car_rental_sensitive_tools", create_tool_node_with_fallback(tools.CAR_RENTAL_SENSITIVE_TOOLS))
    graph.add_edge("book_car_rental_safe_tools", "book_car_rental")
    graph.add_edge("book_car_rental_sensitive_tools", "book_car_rental")
    graph.add_conditional_edges(
        "book_car_rental",
        _make_specialist_router(
            {t.name for t in tools.CAR_RENTAL_SAFE_TOOLS},
            {t.name for t in tools.CAR_RENTAL_SENSITIVE_TOOLS},
            "book_car_rental_safe_tools",
            "book_car_rental_sensitive_tools",
        ),
        ["book_car_rental_safe_tools", "book_car_rental_sensitive_tools", "leave_skill", END],
    )

    # Hotels Specialist
    graph.add_node("enter_book_hotel", create_entry_node("Hotel Booking Specialist", "book_hotel"))
    graph.add_node("book_hotel", AssistantWrapper(hotel_runnable))
    graph.add_edge("enter_book_hotel", "book_hotel")
    graph.add_node("book_hotel_safe_tools", create_tool_node_with_fallback(tools.HOTEL_SAFE_TOOLS))
    graph.add_node("book_hotel_sensitive_tools", create_tool_node_with_fallback(tools.HOTEL_SENSITIVE_TOOLS))
    graph.add_edge("book_hotel_safe_tools", "book_hotel")
    graph.add_edge("book_hotel_sensitive_tools", "book_hotel")
    graph.add_conditional_edges(
        "book_hotel",
        _make_specialist_router(
            {t.name for t in tools.HOTEL_SAFE_TOOLS},
            {t.name for t in tools.HOTEL_SENSITIVE_TOOLS},
            "book_hotel_safe_tools",
            "book_hotel_sensitive_tools",
        ),
        ["book_hotel_safe_tools", "book_hotel_sensitive_tools", "leave_skill", END],
    )

    # Excursions Specialist
    graph.add_node("enter_book_excursion", create_entry_node("Excursion Specialist", "book_excursion"))
    graph.add_node("book_excursion", AssistantWrapper(excursion_runnable))
    graph.add_edge("enter_book_excursion", "book_excursion")
    graph.add_node("book_excursion_safe_tools", create_tool_node_with_fallback(tools.EXCURSION_SAFE_TOOLS))
    graph.add_node("book_excursion_sensitive_tools", create_tool_node_with_fallback(tools.EXCURSION_SENSITIVE_TOOLS))
    graph.add_edge("book_excursion_safe_tools", "book_excursion")
    graph.add_edge("book_excursion_sensitive_tools", "book_excursion")
    graph.add_conditional_edges(
        "book_excursion",
        _make_specialist_router(
            {t.name for t in tools.EXCURSION_SAFE_TOOLS},
            {t.name for t in tools.EXCURSION_SENSITIVE_TOOLS},
            "book_excursion_safe_tools",
            "book_excursion_sensitive_tools",
        ),
        ["book_excursion_safe_tools", "book_excursion_sensitive_tools", "leave_skill", END],
    )

    # Leave Skill
    graph.add_node("leave_skill", pop_dialog_state)
    graph.add_edge("leave_skill", "primary_assistant")

    # Primary Assistant
    graph.add_node("primary_assistant", AssistantWrapper(primary_runnable))
    graph.add_node("primary_assistant_tools", create_tool_node_with_fallback(tools.PRIMARY_ASSISTANT_TOOLS))
    graph.add_edge("primary_assistant_tools", "primary_assistant")
    graph.add_conditional_edges(
        "primary_assistant",
        _route_primary_assistant,
        [
            "enter_update_flight",
            "enter_book_car_rental",
            "enter_book_hotel",
            "enter_book_excursion",
            "primary_assistant_tools",
            END,
        ],
    )

    graph.add_conditional_edges(
        "fetch_user_info",
        _route_to_workflow,
        ["primary_assistant", "update_flight", "book_car_rental", "book_hotel", "book_excursion"],
    )

    return graph.compile(
        checkpointer=CHECKPOINTER,
        interrupt_before=[
            "update_flight_sensitive_tools",
            "book_car_rental_sensitive_tools",
            "book_hotel_sensitive_tools",
            "book_excursion_sensitive_tools",
        ],
    )


# ---------------------------------------------------------------------------
# Registry of All 4 Graphs
# ---------------------------------------------------------------------------

GRAPHS = {
    "part1": build_part1_graph(),
    "part2": build_part2_graph(),
    "part3": build_part3_graph(),
    "part4": build_part4_graph(),
}
