'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { RouteBadge } from '@/components/RouteBadge';
import { MetricsPanel } from '@/components/MetricsPanel';
import { ErrorAlert } from '@/components/ErrorAlert';
import {
  Send,
  Play,
  RotateCcw,
  Copy,
  Check,
  Zap,
  Sparkles,
  Sliders,
  History,
  Info
} from 'lucide-react';

interface RouteResponse {
  status: 'success' | 'degraded_fallback' | 'degraded_error';
  generated_text: string;
  metadata: {
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
  };
  error_details?: string | null;
}

interface HistoryItem {
  id: string;
  timestamp: string;
  prompt: string;
  response: RouteResponse;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function Home() {
  const [prompt, setPrompt] = useState<string>(
    'Provide a quick 2-sentence explanation of quantum entanglement.'
  );
  const [apiStatus, setApiStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [loading, setLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<RouteResponse | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Simulation Controls
  const [simulateGoogleFail, setSimulateGoogleFail] = useState<boolean>(false);
  const [simulateHfFail, setSimulateHfFail] = useState<boolean>(false);
  const [forceRoute, setForceRoute] = useState<'google' | 'huggingface' | null>(null);

  const checkHealth = async () => {
    setApiStatus('checking');
    try {
      const res = await fetch(`${BACKEND_URL}/health`, { cache: 'no-store' });
      if (res.ok) {
        setApiStatus('healthy');
      } else {
        setApiStatus('unhealthy');
      }
    } catch {
      setApiStatus('unhealthy');
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleExecute = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || loading) return;

    setLoading(true);
    setResponse(null);

    try {
      const payload = {
        prompt: prompt.trim(),
        force_route: forceRoute,
        simulate_google_failure: simulateGoogleFail,
        simulate_hf_failure: simulateHfFail,
      };

      const res = await fetch(`${BACKEND_URL}/api/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data: RouteResponse = await res.json();
      setResponse(data);

      // Record History
      const historyEntry: HistoryItem = {
        id: Math.random().toString(36).substring(2, 9),
        timestamp: new Date().toLocaleTimeString(),
        prompt: prompt.trim(),
        response: data,
      };
      setHistory((prev) => [historyEntry, ...prev.slice(0, 9)]);
    } catch (err: any) {
      setResponse({
        status: 'degraded_error',
        generated_text: '⚠️ Network connection failure to backend server.',
        metadata: {
          primary_target: 'unknown',
          final_provider: 'none',
          model_used: 'none',
          reason: 'Network connection failed',
          fallback_activated: true,
          fallback_reason: err.message,
          retries_count: 0,
          latency_ms: 0,
          words_count: prompt.trim().split(/\s+/).length,
          chars_count: prompt.length,
        },
        error_details: `Failed to connect to ${BACKEND_URL}. Ensure Python FastAPI is running.`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (response?.generated_text) {
      navigator.clipboard.writeText(response.generated_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const setSamplePrompt = (sampleText: string, simulateGoogle = false, simulateHf = false) => {
    setPrompt(sampleText);
    setSimulateGoogleFail(simulateGoogle);
    setSimulateHfFail(simulateHf);
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#1F1F1F] flex flex-col">
      <Header apiStatus={apiStatus} onCheckStatus={checkHealth} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Dynamic Target Preview Badge */}
        <RouteBadge prompt={prompt} forceRoute={forceRoute} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Console & Controls */}
          <div className="lg:col-span-2 space-y-6">
            <form onSubmit={handleExecute} className="bg-white p-6 rounded-2xl border border-[#E1E3E1] shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-semibold text-[#1F1F1F] flex items-center gap-2">
                  <Play className="w-4 h-4 text-[#4285F4]" />
                  Enter Prompt for Routing
                </label>
                <span className="text-xs text-[#5F6368]">
                  Rule: &lt;10 words/chars &rarr; Hugging Face | &ge;10 words/chars &rarr; Google API
                </span>
              </div>

              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Type your prompt here..."
                rows={4}
                className="w-full p-4 rounded-xl border border-[#E1E3E1] focus:outline-none focus:ring-2 focus:ring-[#4285F4] focus:border-transparent text-sm bg-white text-[#1F1F1F] transition-all resize-y"
              />

              {/* Preset Sample Prompt Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs font-semibold text-[#5F6368] mr-1">Quick Presets:</span>
                <button
                  type="button"
                  onClick={() => setSamplePrompt('Hello AI')}
                  className="px-2.5 py-1 text-xs rounded-lg bg-green-50 text-[#34A853] border border-green-200 hover:bg-green-100 transition-colors flex items-center gap-1"
                >
                  <Zap className="w-3 h-3" /> Short (&lt;10 words)
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setSamplePrompt(
                      'Please provide a detailed architectural overview of how static and dynamic model routers work in modern generative AI systems.'
                    )
                  }
                  className="px-2.5 py-1 text-xs rounded-lg bg-blue-50 text-[#4285F4] border border-blue-200 hover:bg-blue-100 transition-colors flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3" /> Detailed (&ge;10 words)
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setSamplePrompt(
                      'Explain neural networks and how transformer attention mechanisms work.',
                      true,
                      false
                    )
                  }
                  className="px-2.5 py-1 text-xs rounded-lg bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition-colors"
                >
                  Simulate Google Outage
                </button>
              </div>

              {/* Advanced Controls Accordion */}
              <div className="bg-[#F8F9FA] p-4 rounded-xl border border-gray-200 space-y-3">
                <div className="text-xs font-semibold text-[#5F6368] flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-[#4285F4]" />
                  Failover & Routing Simulation Settings
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <label className="flex items-center gap-2 cursor-pointer text-[#1F1F1F]">
                    <input
                      type="checkbox"
                      checked={simulateGoogleFail}
                      onChange={(e) => setSimulateGoogleFail(e.target.checked)}
                      className="rounded text-[#4285F4] focus:ring-[#4285F4]"
                    />
                    <span>Simulate Google API Error (Triggers Failover)</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer text-[#1F1F1F]">
                    <input
                      type="checkbox"
                      checked={simulateHfFail}
                      onChange={(e) => setSimulateHfFail(e.target.checked)}
                      className="rounded text-[#34A853] focus:ring-[#34A853]"
                    />
                    <span>Simulate Hugging Face API Error</span>
                  </label>
                </div>

                <div className="flex items-center gap-3 pt-1 text-xs">
                  <span className="text-[#5F6368]">Manual Override:</span>
                  <select
                    value={forceRoute || 'auto'}
                    onChange={(e) =>
                      setForceRoute(e.target.value === 'auto' ? null : (e.target.value as any))
                    }
                    className="px-2.5 py-1 rounded-lg border border-gray-300 bg-white text-[#1F1F1F] focus:outline-none focus:ring-1 focus:ring-[#4285F4]"
                  >
                    <option value="auto">Auto Static Routing</option>
                    <option value="google">Force Google API</option>
                    <option value="huggingface">Force Hugging Face</option>
                  </select>
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => setPrompt('')}
                  className="px-3 py-2 text-xs text-[#5F6368] hover:text-[#1F1F1F] flex items-center gap-1 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Clear
                </button>

                <button
                  type="submit"
                  disabled={loading || !prompt.trim()}
                  className="px-6 py-2.5 rounded-xl bg-[#4285F4] hover:bg-blue-600 text-white font-medium text-sm transition-all shadow-xs flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Routing & Requesting...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" /> Run Route Request
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Output Display Card */}
            {response && (
              <div className="bg-white p-6 rounded-2xl border border-[#E1E3E1] shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <h3 className="text-sm font-semibold text-[#1F1F1F] flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#4285F4]" />
                    Model Output Response
                  </h3>
                  <button
                    onClick={handleCopy}
                    className="px-2.5 py-1 text-xs text-[#5F6368] hover:text-[#1F1F1F] hover:bg-gray-100 rounded-lg flex items-center gap-1 transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-[#34A853]" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied!' : 'Copy Text'}
                  </button>
                </div>

                {response.status === 'degraded_error' ? (
                  <ErrorAlert
                    title="Graceful Degradation Notice"
                    message={response.generated_text}
                    details={response.error_details}
                  />
                ) : (
                  <div className="p-4 rounded-xl bg-[#F8F9FA] border border-gray-200 text-sm font-sans whitespace-pre-wrap leading-relaxed text-[#1F1F1F]">
                    {response.generated_text}
                  </div>
                )}

                <MetricsPanel metadata={response.metadata} status={response.status} />
              </div>
            )}
          </div>

          {/* Right Column: Execution History & Architecture Info */}
          <div className="space-y-6">
            {/* Architecture Card */}
            <div className="bg-white p-5 rounded-2xl border border-[#E1E3E1] shadow-xs space-y-3">
              <h3 className="text-sm font-semibold text-[#1F1F1F] flex items-center gap-2">
                <Info className="w-4 h-4 text-[#4285F4]" />
                Routing Architecture Rules
              </h3>

              <div className="space-y-2 text-xs text-[#5F6368]">
                <div className="p-2.5 rounded-lg bg-green-50 border border-green-100 text-green-900">
                  <strong className="text-[#34A853]">Hugging Face Route:</strong> Triggered when word count &lt; 10 OR character count &lt; 10. Uses <code className="font-mono bg-white px-1 py-0.5 rounded text-[#34A853]">Qwen/Qwen2.5-7B-Instruct</code>.
                </div>
                <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-100 text-blue-900">
                  <strong className="text-[#4285F4]">Google API Route:</strong> Triggered when word count &ge; 10 AND character count &ge; 10. Uses <code className="font-mono bg-white px-1 py-0.5 rounded text-[#4285F4]">google/gemini-2.5-flash</code>.
                </div>
                <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-100 text-amber-900">
                  <strong className="text-amber-700">Exponential Backoff & Jitter:</strong> Wrapped with randomized exponential wait retries. Automatically fails over to alternate provider on service disruption.
                </div>
              </div>
            </div>

            {/* Session History Log */}
            <div className="bg-white p-5 rounded-2xl border border-[#E1E3E1] shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                <h3 className="text-sm font-semibold text-[#1F1F1F] flex items-center gap-2">
                  <History className="w-4 h-4 text-[#4285F4]" />
                  Session History Log
                </h3>
                <span className="text-xs text-[#5F6368]">{history.length} runs</span>
              </div>

              {history.length === 0 ? (
                <div className="text-xs text-[#5F6368] text-center py-6">
                  No requests executed yet in this session.
                </div>
              ) : (
                <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => {
                        setPrompt(item.prompt);
                        setResponse(item.response);
                      }}
                      className="p-3 rounded-xl border border-gray-100 hover:border-blue-200 bg-[#F8F9FA] hover:bg-blue-50/50 cursor-pointer transition-all space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span
                          className={`font-semibold ${
                            item.response.metadata.final_provider === 'huggingface'
                              ? 'text-[#34A853]'
                              : 'text-[#4285F4]'
                          }`}
                        >
                          {item.response.metadata.final_provider.toUpperCase()}
                        </span>
                        <span className="text-[#5F6368]">{item.timestamp}</span>
                      </div>
                      <p className="text-xs text-[#1F1F1F] font-medium line-clamp-1">
                        "{item.prompt}"
                      </p>
                      <div className="text-[10px] text-[#5F6368] flex items-center justify-between">
                        <span>{item.response.metadata.latency_ms} ms</span>
                        {item.response.metadata.fallback_activated && (
                          <span className="text-[#FBBC05] font-semibold">Failover</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full bg-white border-t border-[#E1E3E1] py-4 text-center text-xs text-[#5F6368]">
        GenAI Model Router &bull; Google Cloud Ready &bull; Python FastAPI & Next.js TypeScript
      </footer>
    </div>
  );
}
