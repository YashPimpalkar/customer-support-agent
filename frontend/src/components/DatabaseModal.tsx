import React, { useState } from 'react';
import {
  Database,
  X,
  RefreshCw,
  Server,
  CheckCircle,
  ShieldCheck,
} from 'lucide-react';
import type { DatabaseStats } from '../types';

interface DatabaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  stats: DatabaseStats | null;
  onReseed: () => Promise<void>;
  isReseeding: boolean;
  databaseUriDisplay: string;
}

export const DatabaseModal: React.FC<DatabaseModalProps> = ({
  isOpen,
  onClose,
  stats,
  onReseed,
  isReseeding,
  databaseUriDisplay,
}) => {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleReseedClick = async () => {
    try {
      await onReseed();
      setSuccessMessage('Database sample data successfully re-seeded and dates updated!');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 ring-1 ring-cyan-500/30">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-heading text-base font-bold text-white">
                Neon PostgreSQL Database Explorer
              </h3>
              <p className="text-xs text-slate-400">
                Connected to AWS us-east-2 Neon Serverless Instance
              </p>
            </div>
          </div>
          <button
            type="button"
            id="close-db-modal-btn"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="space-y-5 p-6">
          {/* Connection Info */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <div className="flex items-center space-x-2">
                <Server className="h-4 w-4 text-cyan-400" />
                <span className="font-semibold text-slate-300">Target Endpoint</span>
              </div>
              <span className="inline-flex items-center text-emerald-400 font-mono">
                <ShieldCheck className="mr-1 h-3.5 w-3.5" />
                SSL Enabled (Require)
              </span>
            </div>
            <div className="mt-2 rounded-lg bg-slate-900/90 p-2 font-mono text-[11px] text-cyan-300 truncate">
              {databaseUriDisplay}
            </div>
          </div>

          {/* Table Metrics Grid */}
          <div>
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              Live Table Row Counts
            </h4>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {stats &&
                Object.entries(stats).map(([table, count]) => (
                  <div
                    key={table}
                    className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-3"
                  >
                    <div className="text-[10px] uppercase tracking-wider text-slate-400 truncate">
                      {table.replace('_', ' ')}
                    </div>
                    <div className="mt-1 font-heading text-lg font-bold text-white">
                      {count !== undefined ? count : '-'}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Reseed notice / notification */}
          {successMessage && (
            <div className="flex items-center space-x-2 rounded-xl bg-emerald-500/10 p-3 text-xs text-emerald-400 ring-1 ring-emerald-500/30">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 bg-slate-950/40 px-6 py-4">
          <button
            type="button"
            id="reseed-db-btn"
            onClick={handleReseedClick}
            disabled={isReseeding}
            className="flex items-center space-x-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-md transition hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isReseeding ? 'animate-spin' : ''}`} />
            <span>{isReseeding ? 'Seeding...' : 'Reseed & Refresh Dates'}</span>
          </button>

          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-medium text-slate-300 transition hover:bg-slate-700 hover:text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
