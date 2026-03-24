import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { AgentStep } from "../types";

const AGENT_ICONS: Record<string, string> = {
  "Log Analyst": "📋",
  "Metrics Correlator": "📊",
  "Root Cause Investigator": "🔍",
  "Runbook Writer": "📝",
};

function StepCard({ step }: { step: AgentStep }) {
  const [expanded, setExpanded] = useState(false);
  const icon = AGENT_ICONS[step.agent_name] ?? "🤖";
  const isOk = step.status === "completed";

  return (
    <div className="relative pl-8">
      <div className={`absolute left-0 top-1 flex h-6 w-6 items-center justify-center rounded-full text-sm border ${isOk ? "border-green-500/40 bg-green-500/10" : "border-red-500/40 bg-red-500/10"}`}>
        {icon}
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="font-medium text-gray-100">{step.agent_name}</p>
            {step.latency_ms && (
              <p className="text-xs text-gray-500 mt-0.5">{(step.latency_ms / 1000).toFixed(1)}s</p>
            )}
          </div>
          <button
            onClick={() => setExpanded((p) => !p)}
            className="text-gray-400 hover:text-gray-200 transition-colors"
          >
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        </div>

        {expanded && (
          <div className="mt-3 space-y-3">
            {step.input_summary && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Input</p>
                <p className="text-sm text-gray-400 bg-gray-800 rounded p-2">{step.input_summary}</p>
              </div>
            )}
            {step.output && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Output</p>
                <p className="text-sm text-gray-300 bg-gray-800 rounded p-2 whitespace-pre-wrap leading-relaxed">{step.output}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function AgentTimeline({ steps }: { steps: AgentStep[] }) {
  if (!steps.length) return <p className="text-gray-500 text-sm">No agent steps recorded.</p>;

  return (
    <div className="space-y-3 relative">
      <div className="absolute left-3 top-6 bottom-6 w-px bg-gray-800" />
      {steps.map((step) => (
        <StepCard key={step.id} step={step} />
      ))}
    </div>
  );
}
