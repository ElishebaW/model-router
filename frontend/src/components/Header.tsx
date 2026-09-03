'use client';

import React from 'react';
import { Cpu, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

interface HeaderProps {
  apiStatus: 'healthy' | 'unhealthy' | 'checking';
  onCheckStatus: () => void;
}

export const Header: React.FC<HeaderProps> = ({ apiStatus, onCheckStatus }) => {
  return (
    <header className="w-full bg-white border-b border-[#E1E3E1] shadow-xs">
      {/* Google Four-Color Top Accent Bar */}
      <div className="google-accent-bar" />
      
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Logo and App Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-[#4285F4]">
            <Cpu className="w-6 h-6 text-[#4285F4]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-[#1F1F1F] tracking-tight">
                GenAI Model Router
              </h1>
              <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-[#4285F4]">
                Enterprise
              </span>
            </div>
            <p className="text-xs text-[#5F6368]">
              Static Length Routing & Backoff Failover Engine (Google Cloud Ready)
            </p>
          </div>
        </div>

        {/* Backend Health Badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F8F9FA] border border-[#E1E3E1] text-xs font-medium">
            <span className="text-[#5F6368]">Backend API:</span>
            {apiStatus === 'healthy' ? (
              <span className="flex items-center gap-1.5 text-[#34A853]">
                <CheckCircle className="w-3.5 h-3.5 text-[#34A853]" />
                Online
              </span>
            ) : apiStatus === 'unhealthy' ? (
              <span className="flex items-center gap-1.5 text-[#EA4335]">
                <AlertCircle className="w-3.5 h-3.5 text-[#EA4335]" />
                Disconnected
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-[#FBBC05]">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#FBBC05]" />
                Checking...
              </span>
            )}
          </div>

          <button
            onClick={onCheckStatus}
            className="p-2 text-[#5F6368] hover:text-[#1F1F1F] hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh API status"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
