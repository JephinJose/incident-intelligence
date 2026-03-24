import { formatDistanceToNow } from "date-fns";
import { AlertTriangle, CheckCircle, Clock, Loader2, Zap } from "lucide-react";
import { Link } from "react-router-dom";
import { SeverityBadge } from "../components/SeverityBadge";
import { StatusBadge } from "../components/StatusBadge";
import { useIncidentStats, useIncidents } from "../hooks/useIncidents";

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-400">{label}</p>
        <span className={`p-2 rounded-lg ${color}`}>
          <Icon size={16} />
        </span>
      </div>
      <p className="text-3xl font-bold text-gray-100">{value}</p>
    </div>
  );
}

export function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useIncidentStats();
  const { data: incidents, isLoading } = useIncidents({ limit: 10 });

  const mttr = stats?.avg_analysis_time_seconds
    ? `${Math.round(stats.avg_analysis_time_seconds / 60)}m`
    : "—";

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time incident intelligence overview</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total Incidents"
          value={statsLoading ? "…" : (stats?.total ?? 0)}
          icon={Zap}
          color="bg-blue-500/10 text-blue-400"
        />
        <StatCard
          label="Critical"
          value={statsLoading ? "…" : (stats?.by_severity?.critical ?? 0)}
          icon={AlertTriangle}
          color="bg-red-500/10 text-red-400"
        />
        <StatCard
          label="Analyzing"
          value={statsLoading ? "…" : ((stats?.by_status?.analyzing ?? 0) + (stats?.by_status?.received ?? 0))}
          icon={Loader2}
          color="bg-yellow-500/10 text-yellow-400"
        />
        <StatCard
          label="Avg Analysis Time"
          value={statsLoading ? "…" : mttr}
          icon={Clock}
          color="bg-green-500/10 text-green-400"
        />
      </div>

      {/* Recent incidents */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-100">Recent Incidents</h2>
          <Link to="/incidents" className="text-sm text-blue-400 hover:text-blue-300">
            View all →
          </Link>
        </div>

        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-16 text-gray-500">
              <Loader2 size={20} className="animate-spin mr-2" /> Loading…
            </div>
          ) : !incidents?.length ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <CheckCircle size={32} className="mb-3 text-green-500/50" />
              <p>No incidents yet</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wide">
                  <th className="text-left px-5 py-3">Incident</th>
                  <th className="text-left px-4 py-3">Service</th>
                  <th className="text-left px-4 py-3">Severity</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-5 py-3.5">
                      <Link
                        to={`/incidents/${inc.id}`}
                        className="text-gray-200 hover:text-blue-400 font-medium transition-colors line-clamp-1"
                      >
                        {inc.title}
                      </Link>
                      {inc.summary && (
                        <p className="text-gray-500 text-xs mt-0.5 line-clamp-1">{inc.summary}</p>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-gray-400 font-mono text-xs">{inc.service_name}</td>
                    <td className="px-4 py-3.5">
                      <SeverityBadge severity={inc.severity} />
                    </td>
                    <td className="px-4 py-3.5">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="px-4 py-3.5 text-gray-500 text-xs whitespace-nowrap">
                      {formatDistanceToNow(new Date(inc.created_at), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
