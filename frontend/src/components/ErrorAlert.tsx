'use client';

import React from 'react';
import { AlertCircle, HelpCircle } from 'lucide-react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  details?: string | null;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Service Degradation Warning',
  message,
  details
}) => {
  return (
    <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-[#1F1F1F] space-y-2">
      <div className="flex items-center gap-2 text-[#EA4335]">
        <AlertCircle className="w-5 h-5 text-[#EA4335] shrink-0" />
        <h4 className="font-semibold text-sm">{title}</h4>
      </div>

      <p className="text-sm text-gray-700 pl-7">{message}</p>

      {details && (
        <div className="mt-2 pl-7 text-xs font-mono bg-white p-2.5 rounded-lg border border-red-100 text-red-800 break-all">
          {details}
        </div>
      )}

      <div className="pl-7 pt-1 flex items-center gap-1.5 text-xs text-[#5F6368]">
        <HelpCircle className="w-3.5 h-3.5" />
        <span>Check your backend `.env` credentials for Google & HuggingFace keys if running in non-demo mode.</span>
      </div>
    </div>
  );
};
