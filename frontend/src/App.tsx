import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { ChatPanel } from './components/ChatPanel';
import { DashboardPanel } from './components/DashboardPanel';
import { DatabaseModal } from './components/DatabaseModal';
import {
  checkHealth,
  getPassengers,
  getPassengerOverview,
  getFlights,
  getCarRentals,
  getHotels,
  getExcursions,
  getDatabaseStats,
  reseedDatabase,
  sendChatMessage,
  approveAction,
} from './api';
import type {
  Passenger,
  PassengerOverview,
  FlightItem,
  BookedItem,
  ChatMessage,
  DatabaseStats,
} from './types';

export const App: React.FC = () => {
  const [passengers, setPassengers] = useState<Passenger[]>([]);
  const [selectedPassengerId, setSelectedPassengerId] = useState<string>('3442 587242');
  const [overview, setOverview] = useState<PassengerOverview | null>(null);
  const [flights, setFlights] = useState<FlightItem[]>([]);
  const [carRentals, setCarRentals] = useState<BookedItem[]>([]);
  const [hotels, setHotels] = useState<BookedItem[]>([]);
  const [excursions, setExcursions] = useState<BookedItem[]>([]);
  const [dbStats, setDbStats] = useState<DatabaseStats | null>(null);
  const [isDbConnected, setIsDbConnected] = useState<boolean>(true);
  const [modelName, setModelName] = useState<string>('gemini-3.8-flash');
  const [currentMode, setCurrentMode] = useState<string>('part3');

  const [threadId, setThreadId] = useState<string>(() => 'thread_' + Math.random().toString(36).substring(2, 9));
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
  const [isDataLoading, setIsDataLoading] = useState<boolean>(false);
  const [isDbModalOpen, setIsDbModalOpen] = useState<boolean>(false);
  const [isReseeding, setIsReseeding] = useState<boolean>(false);

  // Initial load
  useEffect(() => {
    const initialize = async () => {
      try {
        const health = await checkHealth();
        setIsDbConnected(health.status === 'healthy');
        if (health.model) setModelName(health.model);
        if (health.table_stats) setDbStats(health.table_stats);
      } catch (err) {
        console.error('Health check note:', err);
        setIsDbConnected(false);
      }

      try {
        const passList = await getPassengers();
        if (passList.length > 0) {
          setPassengers(passList);
          // Default to '3442 587242' if present, else first
          const found = passList.find((p) => p.passenger_id === '3442 587242');
          setSelectedPassengerId(found ? found.passenger_id : passList[0].passenger_id);
        }
      } catch (err) {
        console.error('Failed to load passengers:', err);
      }

      loadCatalog();
    };

    initialize();
  }, []);

  // When selected passenger changes, load passenger data & reset chat
  useEffect(() => {
    if (!selectedPassengerId) return;
    loadPassengerData(selectedPassengerId);
  }, [selectedPassengerId]);

  const loadPassengerData = async (passengerId: string) => {
    setIsDataLoading(true);
    try {
      const data = await getPassengerOverview(passengerId);
      setOverview(data);
    } catch (err) {
      console.error('Failed to load passenger overview:', err);
    } finally {
      setIsDataLoading(false);
    }
  };

  const loadCatalog = async () => {
    try {
      const [f, c, h, e, s] = await Promise.all([
        getFlights(undefined, undefined, 30),
        getCarRentals(),
        getHotels(),
        getExcursions(),
        getDatabaseStats(),
      ]);
      setFlights(f);
      setCarRentals(c);
      setHotels(h);
      setExcursions(e);
      setDbStats(s);
    } catch (err) {
      console.error('Catalog load error:', err);
    }
  };

  const handleNewChat = () => {
    setThreadId('thread_' + Math.random().toString(36).substring(2, 9));
    setMessages([]);
  };

  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: 'msg_' + Date.now(),
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
      status: 'completed',
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsChatLoading(true);

    try {
      const resp = await sendChatMessage({
        passenger_id: selectedPassengerId,
        thread_id: threadId,
        message: text,
        mode: currentMode,
      });

      const assistantMsg: ChatMessage = {
        id: 'msg_ai_' + Date.now(),
        role: 'assistant',
        content: resp.message,
        toolCalls: resp.tool_calls,
        createdAt: new Date().toISOString(),
        status: resp.status === 'requires_approval' ? 'pending_approval' : 'completed',
        pendingAction:
          resp.status === 'requires_approval' && resp.action_id && resp.actions
            ? { actionId: resp.action_id, actions: resp.actions }
            : undefined,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh itinerary data in background in case safe tool modified state
      loadPassengerData(selectedPassengerId);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: 'err_' + Date.now(),
        role: 'assistant',
        content: `Error: ${err.message || 'Unable to connect to AI server. Please check backend.'}`,
        createdAt: new Date().toISOString(),
        status: 'completed',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleApproveAction = async (actionId: string, approved: boolean, reason?: string) => {
    setIsChatLoading(true);
    try {
      const resp = await approveAction({
        passenger_id: selectedPassengerId,
        thread_id: threadId,
        action_id: actionId,
        approved,
        reason,
        mode: currentMode,
      });

      // Clear pending action from previous message
      setMessages((prev) =>
        prev.map((m) =>
          m.pendingAction?.actionId === actionId ? { ...m, pendingAction: undefined } : m
        )
      );

      const assistantMsg: ChatMessage = {
        id: 'msg_ai_' + Date.now(),
        role: 'assistant',
        content: resp.message,
        toolCalls: resp.tool_calls,
        createdAt: new Date().toISOString(),
        status: resp.status === 'requires_approval' ? 'pending_approval' : 'completed',
        pendingAction:
          resp.status === 'requires_approval' && resp.action_id && resp.actions
            ? { actionId: resp.action_id, actions: resp.actions }
            : undefined,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh itinerary & catalog to show the updated flight / booking in real time!
      await loadPassengerData(selectedPassengerId);
      await loadCatalog();
    } catch (err: any) {
      console.error('Approve action error:', err);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleReseed = async () => {
    setIsReseeding(true);
    try {
      const stats = await reseedDatabase();
      setDbStats(stats);
      await loadPassengerData(selectedPassengerId);
      await loadCatalog();
    } finally {
      setIsReseeding(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 font-sans text-slate-100">
      {/* Top Navbar */}
      <Navbar
        passengers={passengers}
        selectedPassengerId={selectedPassengerId}
        onSelectPassenger={(id) => {
          setSelectedPassengerId(id);
          handleNewChat();
        }}
        currentMode={currentMode}
        onSelectMode={(mode) => {
          setCurrentMode(mode);
          handleNewChat();
        }}
        onNewChat={handleNewChat}
        onOpenDbModal={() => setIsDbModalOpen(true)}
        isDbConnected={isDbConnected}
        modelName={modelName}
      />

      {/* Main Workspace: 2-Column Responsive Layout */}
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 p-4 sm:p-6 lg:flex-row">
        {/* Left Column: Interactive Chat with Human-In-The-Loop Approval */}
        <div className="h-[750px] w-full lg:w-7/12">
          <ChatPanel
            messages={messages}
            isLoading={isChatLoading}
            currentMode={currentMode}
            onSendMessage={handleSendMessage}
            onApproveAction={handleApproveAction}
          />
        </div>

        {/* Right Column: Live Boarding Pass & Itinerary Dashboard */}
        <div className="h-[750px] w-full lg:w-5/12">
          <DashboardPanel
            overview={overview}
            flights={flights}
            carRentals={carRentals}
            hotels={hotels}
            excursions={excursions}
            isLoading={isDataLoading}
            onRefresh={() => loadPassengerData(selectedPassengerId)}
          />
        </div>
      </main>

      {/* Neon PostgreSQL Database Explorer Modal */}
      <DatabaseModal
        isOpen={isDbModalOpen}
        onClose={() => setIsDbModalOpen(false)}
        stats={dbStats}
        onReseed={handleReseed}
        isReseeding={isReseeding}
        databaseUriDisplay="postgresql://neondb_owner:***@ep-fancy-king-b4pflhay-pooler.c-6.us-east-2.aws.neon.tech/customer_support_agent"
      />
    </div>
  );
};

export default App;
