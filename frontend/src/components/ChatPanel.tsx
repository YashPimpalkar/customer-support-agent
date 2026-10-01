import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  User,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Terminal,
  Bot,
  Workflow,
  Lock,
  Unlock,
  Sliders,
} from 'lucide-react';
import type { ChatMessage } from '../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  currentMode: string;
  onSendMessage: (message: string) => void;
  onApproveAction: (actionId: string, approved: boolean, reason?: string) => void;
}

interface ModePrompt {
  tag: string;
  tagColor: string;
  text: string;
  icon: string;
  hint: string;
}

interface ModeConfig {
  id: string;
  name: string;
  badge: string;
  badgeColor: string;
  description: string;
  behaviorNote: string;
  icon: React.ReactNode;
  prompts: ModePrompt[];
}

const MODE_CONFIGS: Record<string, ModeConfig> = {
  part1: {
    id: 'part1',
    name: 'Part 1: Zero-Shot Direct Execution',
    badge: 'Unconstrained Execution',
    badgeColor: 'bg-purple-500/10 text-purple-400 ring-purple-500/20',
    description: 'All 14 tools execute automatically in a single turn without waiting for human approval.',
    behaviorNote: 'Sensitive operations commit directly to Neon PostgreSQL without confirmation pauses.',
    icon: <Unlock className="h-4 w-4 text-purple-400" />,
    prompts: [
      {
        tag: 'Instant Read',
        tagColor: 'bg-slate-800 text-slate-300',
        text: 'What flights do I have booked right now?',
        icon: '✈️',
        hint: 'Returns your flight LX0002 from Basel to Paris',
      },
      {
        tag: 'Flight Schedule',
        tagColor: 'bg-slate-800 text-slate-300',
        text: 'Search available flights departing from Basel (BSL) to Paris (CDG)',
        icon: '🔍',
        hint: 'Queries live scheduled flights in database',
      },
      {
        tag: 'Policy RAG',
        tagColor: 'bg-slate-800 text-slate-300',
        text: 'What is your baggage allowance policy for economy passengers?',
        icon: '📜',
        hint: 'Vector embedding search over policies.md',
      },
      {
        tag: 'Direct Ticket Change',
        tagColor: 'bg-purple-500/20 text-purple-300',
        text: 'Reschedule my ticket 7240005432906569 to upcoming flight 1461',
        icon: '⚡',
        hint: 'Re-books onto valid flight 1461 immediately without pause',
      },
      {
        tag: 'Direct Car Booking',
        tagColor: 'bg-purple-500/20 text-purple-300',
        text: 'Book car rental 2 (Avis Executive in Basel) for my trip',
        icon: '🚗',
        hint: 'Reserves available vehicle 2 directly in PostgreSQL',
      },
      {
        tag: 'Direct Hotel Booking',
        tagColor: 'bg-purple-500/20 text-purple-300',
        text: 'Book Grand Hotel Les Trois Rois (hotel 1 in Basel)',
        icon: '🏨',
        hint: 'Reserves partner luxury hotel directly',
      },
    ],
  },
  part2: {
    id: 'part2',
    name: 'Part 2: Full Confirmation (Pause All)',
    badge: 'Maximum Strictness',
    badgeColor: 'bg-rose-500/10 text-rose-400 ring-rose-500/20',
    description: 'The agent halts and requires explicit authorization before EVERY tool call, including read-only queries.',
    behaviorNote: 'Observe the agent pause to ask permission even to search flight schedules or read company policies.',
    icon: <Lock className="h-4 w-4 text-rose-400" />,
    prompts: [
      {
        tag: 'Read Query Pauses',
        tagColor: 'bg-rose-500/20 text-rose-300',
        text: 'Check my upcoming flight reservations',
        icon: '🛡️',
        hint: 'Pauses to confirm reading your ticket itinerary',
      },
      {
        tag: 'Policy Read Pauses',
        tagColor: 'bg-rose-500/20 text-rose-300',
        text: 'Look up the airline ticket cancellation and refund policy',
        icon: '🛡️',
        hint: 'Pauses before executing lookup_policy',
      },
      {
        tag: 'Search Pauses',
        tagColor: 'bg-rose-500/20 text-rose-300',
        text: 'Search for available flights from Basel to Paris',
        icon: '✈️',
        hint: 'Pauses to confirm search_flights parameters',
      },
      {
        tag: 'Rental Search Pauses',
        tagColor: 'bg-rose-500/20 text-rose-300',
        text: 'Search for available rental cars in Basel',
        icon: '🚗',
        hint: 'Pauses before querying rental fleet in database',
      },
      {
        tag: 'Hotel Search Pauses',
        tagColor: 'bg-rose-500/20 text-rose-300',
        text: 'Find partner hotels in Basel',
        icon: '🏨',
        hint: 'Pauses before querying partner hotels table',
      },
      {
        tag: 'Sensitive Mod Pauses',
        tagColor: 'bg-rose-500/20 text-rose-300',
        text: 'Rebook my ticket 7240005432906569 to flight 1461',
        icon: '⚠️',
        hint: 'Pauses for ticket change confirmation card',
      },
    ],
  },
  part3: {
    id: 'part3',
    name: 'Part 3: Conditional Interrupt (Recommended)',
    badge: 'Balanced HITL',
    badgeColor: 'bg-emerald-500/10 text-emerald-400 ring-emerald-500/20',
    description: 'Safe read tools run automatically; sensitive write actions (ticket changes, bookings) pause for passenger approval.',
    behaviorNote: 'Queries execute instantly without delay, while sensitive operations present an interactive authorization card.',
    icon: <ShieldAlert className="h-4 w-4 text-emerald-400" />,
    prompts: [
      {
        tag: 'Safe Read (Auto)',
        tagColor: 'bg-emerald-500/20 text-emerald-300',
        text: 'What flights do I have booked right now?',
        icon: '🟢',
        hint: 'Runs immediately with 0 delay (returns LX0002 & LX0112)',
      },
      {
        tag: 'Safe Policy (Auto)',
        tagColor: 'bg-emerald-500/20 text-emerald-300',
        text: 'Can I take a carry-on and personal item on my flight?',
        icon: '🟢',
        hint: 'Immediate semantic policy retrieval without approval delay',
      },
      {
        tag: 'Safe Flight Search',
        tagColor: 'bg-emerald-500/20 text-emerald-300',
        text: 'Search available flights from Basel (BSL) to Paris (CDG)',
        icon: '🔍',
        hint: 'Returns real flights 1459 and 1461 in seconds',
      },
      {
        tag: 'Safe Fleet Search',
        tagColor: 'bg-emerald-500/20 text-emerald-300',
        text: 'Search for available rental cars in Basel',
        icon: '🚗',
        hint: 'Returns Avis Executive and National Car in Basel',
      },
      {
        tag: 'Sensitive Re-book (HITL)',
        tagColor: 'bg-amber-500/20 text-amber-300',
        text: 'Please reschedule my ticket 7240005432906569 to flight 1461',
        icon: '🔴',
        hint: 'Safe check auto-runs; re-booking PAUSES for approval card',
      },
      {
        tag: 'Sensitive Hotel (HITL)',
        tagColor: 'bg-amber-500/20 text-amber-300',
        text: 'Book Grand Hotel Les Trois Rois (hotel 1 in Basel)',
        icon: '🏨',
        hint: 'Safe search auto-runs; booking PAUSES for authorization',
      },
      {
        tag: 'Sensitive Car (HITL)',
        tagColor: 'bg-amber-500/20 text-amber-300',
        text: 'Book car rental 2 (Avis Executive in Basel)',
        icon: '🚗',
        hint: 'Safe search auto-runs; booking PAUSES for authorization',
      },
    ],
  },
  part4: {
    id: 'part4',
    name: 'Part 4: Specialized Multi-Agent Swarm',
    badge: 'Hierarchical Delegation',
    badgeColor: 'bg-cyan-500/10 text-cyan-400 ring-cyan-500/20',
    description: 'Primary router concierge dynamically delegates tasks to 4 domain-isolated specialist agents with a dialog stack.',
    behaviorNote: 'Domain specialists handle their respective workflows and call CompleteOrEscalate to hand control back to the concierge.',
    icon: <Workflow className="h-4 w-4 text-cyan-400" />,
    prompts: [
      {
        tag: 'Flight Specialist',
        tagColor: 'bg-blue-500/20 text-blue-300',
        text: 'I need to speak to the flight updates desk to check my flight status',
        icon: '✈️',
        hint: 'Primary delegates to Flight Specialist; fetches flight LX0002',
      },
      {
        tag: 'Car Specialist',
        tagColor: 'bg-emerald-500/20 text-emerald-300',
        text: 'Connect me to the car rental specialist to find available cars in Basel',
        icon: '🚗',
        hint: 'Delegates to Car Specialist; returns Avis Executive and National Car',
      },
      {
        tag: 'Hotel Specialist',
        tagColor: 'bg-purple-500/20 text-purple-300',
        text: 'Transfer me to the hotel concierge to search luxury hotels in Basel',
        icon: '🏨',
        hint: 'Delegates to Hotel Specialist; returns Grand Hotel Les Trois Rois',
      },
      {
        tag: 'Excursion Specialist',
        tagColor: 'bg-amber-500/20 text-amber-300',
        text: 'Connect me to the excursion guide for scenic tours in Basel',
        icon: '🏔️',
        hint: 'Delegates to Excursion Specialist; returns Rhine Sunset Cruise',
      },
      {
        tag: 'Direct Policy (Router)',
        tagColor: 'bg-cyan-500/20 text-cyan-300',
        text: 'What are your customer support policies regarding baggage allowances?',
        icon: 'ℹ️',
        hint: 'Primary answers directly with lookup_policy without delegating',
      },
      {
        tag: 'Escalate / Pop Stack',
        tagColor: 'bg-slate-700 text-slate-200',
        text: 'I am finished with car rentals, please return to the main concierge',
        icon: '🔄',
        hint: 'Calls CompleteOrEscalate to pop dialog stack back to Primary',
      },
    ],
  },
};

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isLoading,
  currentMode,
  onSendMessage,
  onApproveAction,
}) => {
  const [inputText, setInputText] = useState('');
  const [declineReason, setDeclineReason] = useState<{ [actionId: string]: string }>({});
  const [showDeclineInput, setShowDeclineInput] = useState<{ [actionId: string]: boolean }>({});
  const [showQuickOptions, setShowQuickOptions] = useState<boolean>(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeModeConfig = MODE_CONFIGS[currentMode] || MODE_CONFIGS.part3;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    const text = inputText.trim();
    setInputText('');
    onSendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const handleSelectPrompt = (promptText: string) => {
    if (isLoading) return;
    onSendMessage(promptText);
  };

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-800/80 bg-slate-900/60 shadow-2xl backdrop-blur-xl">
      {/* Chat Header & Active Mode Indicator */}
      <div className="border-b border-slate-800/80 px-6 py-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="font-heading text-base font-semibold text-white">
                  AI Support Concierge
                </h2>
                <span
                  className={`inline-flex items-center space-x-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${activeModeConfig.badgeColor}`}
                >
                  {activeModeConfig.icon}
                  <span>{activeModeConfig.badge}</span>
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {activeModeConfig.name}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="flex items-center space-x-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 ring-1 ring-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Online</span>
            </span>
          </div>
        </div>

        {/* Mode Behavior Subtitle */}
        <div className="mt-2.5 rounded-xl border border-slate-800/80 bg-slate-950/40 px-3 py-1.5 text-xs text-slate-300">
          <span className="font-medium text-cyan-300">Architecture: </span>
          {activeModeConfig.description}{' '}
          <span className="text-slate-400">({activeModeConfig.behaviorNote})</span>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">
        {messages.length === 0 ? (
          <div className="my-auto flex flex-col items-center justify-center py-6 text-center">
            <div className="relative mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-blue-500/20 p-3 ring-1 ring-cyan-500/30">
              <Bot className="h-7 w-7 text-cyan-400" />
            </div>
            <h3 className="font-heading text-base font-bold text-white">
              Tailored Test Options for {activeModeConfig.name}
            </h3>
            <p className="mt-1 max-w-md text-xs text-slate-400">
              Select one of the mode-specific prompts below to test how this architecture handles tool execution, interrupts, or delegation:
            </p>

            {/* Mode-Specific Starter Cards */}
            <div className="mt-5 grid max-w-2xl grid-cols-1 gap-2.5 sm:grid-cols-2 text-left">
              {activeModeConfig.prompts.map((starter, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectPrompt(starter.text)}
                  className="group flex flex-col rounded-xl border border-slate-800 bg-slate-800/40 p-3 text-left transition hover:border-cyan-500/40 hover:bg-slate-800/80 hover:shadow-lg hover:shadow-cyan-500/5 active:scale-98"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-base">{starter.icon}</span>
                    <span
                      className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${starter.tagColor}`}
                    >
                      {starter.tag}
                    </span>
                  </div>
                  <div className="mt-2 text-xs font-semibold text-slate-200 group-hover:text-cyan-300">
                    {starter.text}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400">
                    {starter.hint}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`flex max-w-[88%] items-start space-x-3 sm:max-w-[80%] ${
                  msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-cyan-500/20'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                </div>

                {/* Message Bubble */}
                <div className="space-y-2">
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                        : 'border border-slate-800 bg-slate-800/80 text-slate-100 backdrop-blur-sm'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>

                    {/* Tool Badges */}
                    {msg.toolCalls && msg.toolCalls.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5 border-t border-slate-700/60 pt-2">
                        {msg.toolCalls.map((toolName, tIdx) => (
                          <span
                            key={tIdx}
                            className="inline-flex items-center rounded-md bg-slate-900/90 px-2 py-0.5 text-[11px] font-mono font-medium text-cyan-300 ring-1 ring-cyan-500/30"
                          >
                            <Terminal className="mr-1 h-3 w-3 text-cyan-400" />
                            {toolName}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* HUMAN-IN-THE-LOOP APPROVAL CARD */}
                  {msg.pendingAction && (
                    <div className="overflow-hidden rounded-2xl border border-amber-500/40 bg-gradient-to-b from-amber-500/10 to-slate-900/90 p-4 shadow-xl ring-1 ring-amber-500/20">
                      <div className="flex items-center space-x-2 text-amber-400">
                        <ShieldAlert className="h-5 w-5 animate-bounce" />
                        <span className="font-heading text-sm font-bold uppercase tracking-wider">
                          Human Authorization Required
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-300">
                        The AI assistant has halted execution before sensitive write tools.
                        Please review the requested action below:
                      </p>

                      {/* Action Details */}
                      <div className="my-3 space-y-2 rounded-xl border border-amber-500/20 bg-slate-950/60 p-3">
                        {msg.pendingAction.actions.map((act, actIdx) => (
                          <div key={actIdx} className="space-y-1">
                            <div className="flex items-center space-x-2 text-xs font-semibold text-white">
                              <ChevronRight className="h-3.5 w-3.5 text-amber-400" />
                              <span>{act.description}</span>
                            </div>
                            <div className="rounded-lg bg-slate-900/90 p-2 font-mono text-[11px] text-slate-300">
                              <span className="text-amber-300">Tool: {act.name}</span>
                              <pre className="mt-1 overflow-x-auto text-[10px] text-slate-400">
                                {JSON.stringify(act.args, null, 2)}
                              </pre>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Approval Buttons */}
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <button
                          type="button"
                          id={`approve-btn-${msg.pendingAction.actionId}`}
                          onClick={() =>
                            onApproveAction(msg.pendingAction!.actionId, true)
                          }
                          className="flex items-center space-x-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-emerald-600/30 transition hover:from-emerald-500 hover:to-teal-500 active:scale-95"
                        >
                          <CheckCircle2 className="h-4 w-4" />
                          <span>Approve & Execute</span>
                        </button>

                        <button
                          type="button"
                          id={`deny-toggle-btn-${msg.pendingAction.actionId}`}
                          onClick={() =>
                            setShowDeclineInput((prev) => ({
                              ...prev,
                              [msg.pendingAction!.actionId]: !prev[msg.pendingAction!.actionId],
                            }))
                          }
                          className="flex items-center space-x-1.5 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3.5 py-2 text-xs font-medium text-rose-300 transition hover:bg-rose-500/20 active:scale-95"
                        >
                          <XCircle className="h-4 w-4" />
                          <span>Decline / Suggest Change</span>
                        </button>
                      </div>

                      {/* Inline Decline Feedback Input */}
                      {showDeclineInput[msg.pendingAction.actionId] && (
                        <div className="mt-3 flex items-center space-x-2 border-t border-slate-800/80 pt-3">
                          <input
                            type="text"
                            placeholder="Reason for declining (e.g. 'I prefer a flight next week instead')"
                            value={declineReason[msg.pendingAction.actionId] || ''}
                            onChange={(e) =>
                              setDeclineReason((prev) => ({
                                ...prev,
                                [msg.pendingAction!.actionId]: e.target.value,
                              }))
                            }
                            className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-rose-400"
                          />
                          <button
                            type="button"
                            onClick={() =>
                              onApproveAction(
                                msg.pendingAction!.actionId,
                                false,
                                declineReason[msg.pendingAction!.actionId]
                              )
                            }
                            className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-rose-500"
                          >
                            Send Decline
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  <div
                    className={`text-[10px] text-slate-500 ${
                      msg.role === 'user' ? 'text-right' : 'text-left'
                    }`}
                  >
                    {new Date(msg.createdAt).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center space-x-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400">
              <Sparkles className="h-4 w-4 animate-spin text-cyan-400" />
            </div>
            <div className="flex items-center space-x-2 rounded-2xl border border-slate-800 bg-slate-800/60 px-4 py-3">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping"></span>
              <span className="text-xs font-medium text-slate-300">
                Agent reasoning across Neon PostgreSQL tools...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Mode-Specific Quick Input Presets Carousel / Drawer */}
      <div className="border-t border-slate-800/80 bg-slate-950/80 px-4 py-2">
        <div className="flex items-center justify-between pb-1.5">
          <div className="flex items-center space-x-1.5 text-[11px] font-medium text-slate-400">
            <Sliders className="h-3.5 w-3.5 text-cyan-400" />
            <span>Mode Input Presets:</span>
            <span className="font-semibold text-slate-300">{activeModeConfig.name.split(':')[0]}</span>
          </div>
          <button
            type="button"
            onClick={() => setShowQuickOptions((v) => !v)}
            className="text-[11px] font-medium text-cyan-400 hover:text-cyan-300"
          >
            {showQuickOptions ? 'Hide' : 'Show Presets'}
          </button>
        </div>

        {showQuickOptions && (
          <div className="flex space-x-2 overflow-x-auto py-1 scrollbar-thin">
            {activeModeConfig.prompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectPrompt(p.text)}
                disabled={isLoading}
                title={p.hint}
                className="flex shrink-0 items-center space-x-1.5 rounded-lg border border-slate-800 bg-slate-900/90 px-2.5 py-1.5 text-xs text-slate-300 transition hover:border-cyan-500/40 hover:bg-slate-800 hover:text-white disabled:opacity-40"
              >
                <span>{p.icon}</span>
                <span className="font-medium">{p.text}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Input Form */}
      <div className="border-t border-slate-800/80 bg-slate-950/60 p-3 sm:p-4">
        <form onSubmit={handleSend} className="relative flex items-center">
          <textarea
            id="chat-input"
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Ask ${activeModeConfig.name.split(':')[0]} a question or select a preset above... (Enter to send)`}
            disabled={isLoading}
            className="w-full resize-none rounded-xl border border-slate-800 bg-slate-900/90 py-3 pl-4 pr-24 text-sm text-slate-100 placeholder-slate-500 shadow-inner outline-none transition focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 disabled:opacity-50"
          />
          <button
            type="submit"
            id="send-message-btn"
            disabled={!inputText.trim() || isLoading}
            className="absolute right-2 flex items-center space-x-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-cyan-500/20 transition hover:from-cyan-400 hover:to-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <span>Send</span>
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
