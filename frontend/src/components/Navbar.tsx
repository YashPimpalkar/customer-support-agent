import React from 'react';
import {
  Plane,
  Database,
  User,
  RotateCcw,
  Sparkles,
  ChevronDown,
} from 'lucide-react';
import type { Passenger } from '../types';

interface NavbarProps {
  passengers: Passenger[];
  selectedPassengerId: string;
  onSelectPassenger: (id: string) => void;
  currentMode: string;
  onSelectMode: (mode: string) => void;
  onNewChat: () => void;
  onOpenDbModal: () => void;
  isDbConnected: boolean;
  modelName: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  passengers,
  selectedPassengerId,
  onSelectPassenger,
  currentMode,
  onSelectMode,
  onNewChat,
  onOpenDbModal,
  isDbConnected,
  modelName,
}) => {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand & AI badge */}
        <div className="flex items-center space-x-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20">
            <Plane className="h-5 w-5 text-white" />
            <span className="absolute -bottom-1 -right-1 flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex h-3 w-3 rounded-full bg-cyan-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-heading text-xl font-bold tracking-tight text-white">
                Aero<span className="text-cyan-400">Assist</span>
              </span>
              <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-2 py-0.5 text-xs font-medium text-cyan-300 ring-1 ring-inset ring-cyan-500/20">
                <Sparkles className="mr-1 h-3 w-3 text-cyan-400" />
                {modelName}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Swiss Air Demo • LangGraph (Parts 1-4) & Neon PostgreSQL
            </p>
          </div>
        </div>

        {/* Center / Right controls */}
        <div className="flex items-center space-x-3">
          {/* Mode Selector (Part 1, 2, 3, 4) */}
          <div className="relative">
            <label htmlFor="mode-select" className="sr-only">
              Select Agent Architecture
            </label>
            <div className="flex items-center space-x-2 rounded-xl border border-slate-800 bg-slate-900/90 px-3 py-1.5 shadow-inner">
              <span className="flex h-2 w-2 rounded-full bg-cyan-400"></span>
              <div className="text-left">
                <div className="text-[10px] uppercase tracking-wider text-slate-400">
                  Agent Mode
                </div>
                <div className="relative flex items-center">
                  <select
                    id="mode-select"
                    value={currentMode}
                    onChange={(e) => onSelectMode(e.target.value)}
                    className="cursor-pointer appearance-none bg-transparent pr-6 text-xs font-semibold text-cyan-300 outline-none hover:text-cyan-200"
                  >
                    <option value="part1" className="bg-slate-900 text-slate-200">
                      Part 1: Zero-Shot (No Approval)
                    </option>
                    <option value="part2" className="bg-slate-900 text-slate-200">
                      Part 2: Full Confirmation (Pause All)
                    </option>
                    <option value="part3" className="bg-slate-900 text-slate-200">
                      Part 3: Conditional Interrupt (Recommended)
                    </option>
                    <option value="part4" className="bg-slate-900 text-slate-200">
                      Part 4: Specialized Multi-Agent
                    </option>
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-0 h-3 w-3 text-slate-400" />
                </div>
              </div>
            </div>
          </div>
          {/* Passenger Selector */}
          <div className="relative">
            <label
              htmlFor="passenger-select"
              className="sr-only"
            >
              Select Active Passenger
            </label>
            <div className="flex items-center space-x-2 rounded-xl border border-slate-800 bg-slate-900/90 px-3 py-1.5 shadow-inner">
              <User className="h-4 w-4 text-cyan-400" />
              <div className="text-left">
                <div className="text-[10px] uppercase tracking-wider text-slate-400">
                  Active Passenger
                </div>
                <div className="relative flex items-center">
                  <select
                    id="passenger-select"
                    value={selectedPassengerId}
                    onChange={(e) => onSelectPassenger(e.target.value)}
                    className="cursor-pointer appearance-none bg-transparent pr-6 text-xs font-semibold text-slate-200 outline-none hover:text-white"
                  >
                    {passengers.map((p, idx) => (
                      <option
                        key={`${p.passenger_id}-${p.flight_no || p.ticket_no || idx}-${idx}`}
                        value={p.passenger_id}
                        className="bg-slate-900 text-slate-200"
                      >
                        {p.passenger_name || 'Passenger'} ({p.passenger_id})
                        {p.flight_no ? ` - ${p.flight_no}` : ''}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-0 h-3 w-3 text-slate-400" />
                </div>
              </div>
            </div>
          </div>

          {/* PostgreSQL Status Button */}
          <button
            id="db-inspector-btn"
            type="button"
            onClick={onOpenDbModal}
            className="flex items-center space-x-2 rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-slate-700 hover:bg-slate-800/80 hover:text-white"
            title="Inspect Neon PostgreSQL tables and metrics"
          >
            <span className="relative flex h-2 w-2">
              <span
                className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                  isDbConnected ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              ></span>
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${
                  isDbConnected ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              ></span>
            </span>
            <Database className="h-3.5 w-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Neon DB</span>
          </button>

          {/* Reset / New Session */}
          <button
            id="new-session-btn"
            type="button"
            onClick={onNewChat}
            className="flex items-center space-x-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 px-3 py-2 text-xs font-semibold text-white shadow-md shadow-cyan-600/20 transition hover:from-cyan-500 hover:to-blue-500 hover:shadow-cyan-500/30 active:scale-95"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">New Session</span>
          </button>
        </div>
      </div>
    </header>
  );
};
