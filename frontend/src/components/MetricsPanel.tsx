'use client';

import React from 'react';
import { Clock, RefreshCw, AlertTriangle, Layers, Award } from 'lucide-react';

interface Metadata {
  primary_target: string;
  final_provider: string;
  model_used: string;
  reason: string;
  fallback_activated: boolean;
  fallback_reason?: string | null;
  retries_count: number;
  latency_ms: number;
  words_count: number;
  chars_count: number;
}

interface MetricsPanelProps {
  metadata?: Metadata | null;
  status?: string;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metadata, status }) => {
  if (!metadata) return null;

  const isFallback = metadata.fallback_activated;
  const isError = status === 'degraded_error';

  return (
    <div className="bg-white p-5 rounded-2xl border border-[#E1E3E1] shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <h3 className="text-sm font-semibold text-[#1F1F1F] flex items-center gap-2">
          <Layers className="w-4 h-4 text-[#4285F4]" />
          Execution Metadata & Metrics
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            isError
              ? 'bg-red-100 text-[#EA4335]'
              : isFallback
              ? 'bg-amber-100 text-[#FBBC05]'
              : 'bg-green-100 text-[#34A853]'
          }`}
        >
          {isError ? 'Degraded Error' : isFallback ? 'Failover Triggered' : 'Success'}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Metric 1: Provider Used */}
        <div className="bg-[#F8F9FA] p-3 rounded-xl border border-gray-200">
          <div className="text-xs text-[#5F6368] mb-1">Provider Used</div>
          <div className="text-sm font-bold text-[#1F1F1F] capitalize flex items-center gap-1.5">
            <Award className="w-4 h-4 text-[#4285F4]" />
            {metadata.final_provider}
          </div>
          <div className="text-[11px] text-[#5F6368] truncate mt-0.5" title={metadata.model_used}>
            {metadata.model_used}
          </div>
        </div>

        {/* Metric 2: Latency */}
        <div className="bg-[#F8F9FA] p-3 rounded-xl border border-gray-200">
          <div className="text-xs text-[#5F6368] mb-1">Response Latency</div>
          <div className="text-sm font-bold text-[#1F1F1F] flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-[#34A853]" />
            {metadata.latency_ms} ms
          </div>
          <div className="text-[11px] text-[#5F6368] mt-0.5">Total round-trip time</div>
        </div>

        {/* Metric 3: Retries */}
        <div className="bg-[#F8F9FA] p-3 rounded-xl border border-gray-200">
          <div className="text-xs text-[#5F6368] mb-1">Backoff Retries</div>
          <div className="text-sm font-bold text-[#1F1F1F] flex items-center gap-1.5">
            <RefreshCw className="w-4 h-4 text-[#FBBC05]" />
            {metadata.retries_count} retry{metadata.retries_count === 1 ? '' : 's'}
          </div>
          <div className="text-[11px] text-[#5F6368] mt-0.5">Jittered backoff</div>
        </div>

        {/* Metric 4: Fallback Status */}
        <div className="bg-[#F8F9FA] p-3 rounded-xl border border-gray-200">
          <div className="text-xs text-[#5F6368] mb-1">Failover Status</div>
          <div className="text-sm font-bold text-[#1F1F1F] flex items-center gap-1.5">
            {isFallback ? (
              <span className="text-[#FBBC05] flex items-center gap-1">
                <AlertTriangle className="w-4 h-4 text-[#FBBC05]" /> Active
              </span>
            ) : (
              <span className="text-[#34A853]">Direct</span>
            )}
          </div>
          <div className="text-[11px] text-[#5F6368] mt-0.5">
            Target: {metadata.primary_target}
          </div>
        </div>
      </div>

      {/* Fallback Cause Alert */}
      {isFallback && metadata.fallback_reason && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-[#FBBC05] shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Automatic Failover Event:</span> {metadata.fallback_reason}
          </div>
        </div>
      )}
    </div>
  );
};
