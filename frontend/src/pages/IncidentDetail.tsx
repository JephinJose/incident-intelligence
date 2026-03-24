import { formatDistanceToNow, format } from "date-fns";
import { ArrowLeft, Copy, Loader2, RefreshCw } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";
import { incidentsApi } from "../api/client";
import { AgentTimeline } from "../components/AgentTimeline";
import { SeverityBadge } from "../components/SeverityBadge";
import { StatusBadge } from "../components/StatusBadge";
import { useIncident } from "../hooks/useIncidents";

type Tab = "summary" | "agents" | "runbook" | "raw";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={copy}
      className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 transition-colors px-2.5 py-1 rounded border border-gray-700 hover:border-gray-500"
    >
      <Copy size={12} />
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

export function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const incidentId = Number(id);
  const { data: incident, isLoading } = useIncident(incidentId);
  const [activeTab, setActiveTab] = useState<Tab>("summary");
  const [triggering, setTriggering] = useState(false);

  const triggerAnalysis = async () => {
    setTriggering(true);
    try {
      await incidentsApi.triggerAnalysis(incidentId);
    } finally {
      setTriggering(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <Loader2 size={24} className="animate-spin mr-2" /> Loading…
      </div>
    );
  }

  if (!incident) {
    return <div className="p-8 text-gray-400">Incident not found.</div>;
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "summary", label: "Summary" },
    { id: "agents", label: `Agent Steps (${incident.agent_steps.length})` },
    { id: "runbook", label: "Runbook" },
    { id: "raw", label: "Raw Payload" },
  ];

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      {/* Back */}
      <Link to="/incidents" className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors w-fit">
        <ArrowLeft size={14} /> Back to incidents
      </Link>

      {/* Header */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-100 mb-3">{incident.title}</h1>
            <div className="flex flex-wrap items-center gap-3">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <span className="text-xs text-gray-500 font-mono bg-gray-800 px-2 py-0.5 rounded">{incident.service_name}</span>
              <span className="text-xs text-gray-500 capitalize">{incident.source}</span>
            </div>
          </div>
          {(incident.status === "failed" || incident.status === "received") && (
            <button
              onClick={triggerAnalysis}
              disabled={triggering}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm transition-colors disabled:opacity-50"
            >
              <RefreshCw size={14} className={triggering ? "animate-spin" : ""} />
              Re-analyze
            </button>
          )}
        </div>

        <div className="mt-4 flex gap-6 text-xs text-gray-500">
          <span>Created {format(new Date(incident.created_at), "MMM d, yyyy HH:mm")}</span>
          {incident.analyzed_at && (
            <span>Analyzed {formatDistanceToNow(new Date(incident.analyzed_at), { addSuffix: true })}</span>
          )}
          {incident.confidence != null && (
            <span>Confidence: <span className="text-gray-300 font-semibold">{Math.round(incident.confidence * 100)}%</span></span>
          )}
        </div>

        {incident.error_message && (
          <div className="mt-4 rounded-lg bg-red-500/10 border border-red-500/30 p-3 text-sm text-red-400">
            {incident.error_message}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-800">
        <div className="flex gap-0">
          {tabs.map(({ id: tid, label }) => (
            <button
              key={tid}
              onClick={() => setActiveTab(tid)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tid
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "summary" && (
        <div className="space-y-4">
          {incident.status === "analyzing" || incident.status === "received" ? (
            <div className="flex items-center gap-3 text-gray-400 py-12 justify-center">
              <Loader2 size={20} className="animate-spin" />
              <span>AI agents are analyzing this incident…</span>
            </div>
          ) : (
            <>
              {incident.summary && (
                <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
                  <h3 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wide">Summary</h3>
                  <p className="text-gray-200 leading-relaxed">{incident.summary}</p>
                </div>
              )}
              {incident.root_cause && (
                <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-5">
                  <h3 className="text-sm font-semibold text-orange-400 mb-2 uppercase tracking-wide">Root Cause</h3>
                  <p className="text-gray-200 leading-relaxed">{incident.root_cause}</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                {incident.log_analysis && (
                  <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
                    <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wide">Log Analysis</h3>
                    <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{incident.log_analysis}</p>
                  </div>
                )}
                {incident.metrics_analysis && (
                  <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
                    <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wide">Metrics Analysis</h3>
                    <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{incident.metrics_analysis}</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === "agents" && (
        <AgentTimeline steps={incident.agent_steps} />
      )}

      {activeTab === "runbook" && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          {incident.runbook ? (
            <>
              <div className="flex justify-end mb-4">
                <CopyButton text={incident.runbook} />
              </div>
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{incident.runbook}</ReactMarkdown>
              </div>
            </>
          ) : (
            <p className="text-gray-500 text-center py-8">
              {incident.status === "analyzed" ? "No runbook generated." : "Runbook will appear after analysis completes."}
            </p>
          )}
        </div>
      )}

      {activeTab === "raw" && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <div className="flex justify-end mb-3">
            <CopyButton text={JSON.stringify(incident.alert_payload, null, 2)} />
          </div>
          <pre className="text-xs text-gray-300 overflow-x-auto leading-relaxed">
            {JSON.stringify(incident.alert_payload, null, 2)}
          </pre>
          {incident.log_snippets.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Log Snippets</p>
              {incident.log_snippets.map((log, i) => (
                <p key={i} className="text-xs font-mono text-gray-400 py-0.5">{log}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
