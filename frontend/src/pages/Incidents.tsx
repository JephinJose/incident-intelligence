import { formatDistanceToNow } from "date-fns";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { SeverityBadge } from "../components/SeverityBadge";
import { StatusBadge } from "../components/StatusBadge";
import { useIncidents } from "../hooks/useIncidents";
import type { Severity } from "../types";

const SEVERITIES: Array<Severity | ""> = ["", "critical", "high", "medium", "low"];
const STATUSES = ["", "received", "analyzing", "analyzed", "failed"];

export function Incidents() {
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [service, setService] = useState("");

  const filters: Record<string, string> = {};
  if (severity) filters.severity = severity;
  if (status) filters.status = status;
  if (service) filters.service = service;

  const { data: incidents, isLoading } = useIncidents(filters);

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Incidents</h1>
        <p className="text-gray-400 text-sm mt-1">{incidents?.length ?? 0} results</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <input
          value={service}
          onChange={(e) => setService(e.target.value)}
          placeholder="Filter by service…"
          className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 w-48"
        />
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        >
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>{s || "All severities"}</option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s || "All statuses"}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20 text-gray-500">
            <Loader2 size={20} className="animate-spin mr-2" /> Loading…
          </div>
        ) : !incidents?.length ? (
          <div className="text-center py-20 text-gray-500">No incidents match your filters</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wide">
                <th className="text-left px-5 py-3">Title</th>
                <th className="text-left px-4 py-3">Service</th>
                <th className="text-left px-4 py-3">Severity</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Confidence</th>
                <th className="text-left px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {incidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-gray-800/50 transition-colors">
                  <td className="px-5 py-4 max-w-xs">
                    <Link
                      to={`/incidents/${inc.id}`}
                      className="text-gray-200 hover:text-blue-400 font-medium transition-colors block truncate"
                    >
                      {inc.title}
                    </Link>
                  </td>
                  <td className="px-4 py-4 text-gray-400 font-mono text-xs">{inc.service_name}</td>
                  <td className="px-4 py-4"><SeverityBadge severity={inc.severity} /></td>
                  <td className="px-4 py-4"><StatusBadge status={inc.status} /></td>
                  <td className="px-4 py-4 text-gray-400">
                    {inc.confidence != null ? `${Math.round(inc.confidence * 100)}%` : "—"}
                  </td>
                  <td className="px-4 py-4 text-gray-500 text-xs whitespace-nowrap">
                    {formatDistanceToNow(new Date(inc.created_at), { addSuffix: true })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
