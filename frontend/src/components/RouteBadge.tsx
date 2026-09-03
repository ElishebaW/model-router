'use client';

import React from 'react';
import { ArrowRight, Sparkles, Zap, ShieldCheck } from 'lucide-react';

interface RouteBadgeProps {
  prompt: string;
  forceRoute?: 'google' | 'huggingface' | null;
}

export const RouteBadge: React.FC<RouteBadgeProps> = ({ prompt, forceRoute }) => {
  const cleaned = prompt.trim();
  const words = cleaned ? cleaned.split(/\s+/).length : 0;
  const chars = cleaned.length;

  const isShortWords = words < 10;
  const isShortChars = chars < 10;
  const isHF = isShortWords || isShortChars;

  const target = forceRoute || (isHF ? 'huggingface' : 'google');

  return (
    <div className="bg-white p-4 rounded-2xl border border-[#E1E3E1] shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all">
      <div className="flex items-center gap-3">
        <div
          className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white transition-colors ${
            target === 'huggingface'
              ? 'bg-[#34A853]'
              : 'bg-[#4285F4]'
          }`}
        >
          {target === 'huggingface' ? <Zap className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5F6368]">
              Estimated Target Route:
            </span>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                target === 'huggingface'
                  ? 'bg-green-100 text-[#34A853]'
                  : 'bg-blue-100 text-[#4285F4]'
              }`}
            >
              {target === 'huggingface' ? 'Hugging Face API' : 'Google API'}
            </span>
          </div>
          <p className="text-sm font-medium text-[#1F1F1F]">
            {target === 'huggingface'
              ? 'Qwen/Qwen2.5-7B-Instruct'
              : 'google/gemini-2.5-flash'}
          </p>
        </div>
      </div>

      {/* Counters & Rule Reason */}
      <div className="flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#F8F9FA] border border-gray-200">
          <span className="text-[#5F6368]">Words:</span>
          <span className={`font-semibold ${isShortWords ? 'text-[#EA4335]' : 'text-[#34A853]'}`}>
            {words} / 10
          </span>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#F8F9FA] border border-gray-200">
          <span className="text-[#5F6368]">Chars:</span>
          <span className={`font-semibold ${isShortChars ? 'text-[#EA4335]' : 'text-[#34A853]'}`}>
            {chars} / 10
          </span>
        </div>

        <div className="hidden md:flex items-center gap-1 text-[#5F6368]">
          <ShieldCheck className="w-4 h-4 text-[#4285F4]" />
          <span>
            {forceRoute
              ? `Override active (${forceRoute})`
              : isHF
              ? 'Static rule: <10 words/chars -> HF'
              : 'Static rule: >=10 words/chars -> Google'}
          </span>
        </div>
      </div>
    </div>
  );
};
