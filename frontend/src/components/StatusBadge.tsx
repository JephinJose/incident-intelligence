import type { IncidentStatus } from "../types";

const styles: Record<IncidentStatus, string> = {
  received: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  analyzing: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  analyzed: "bg-green-500/20 text-green-400 border-green-500/30",
  failed: "bg-red-500/20 text-red-400 border-red-500/30",
};

export function StatusBadge({ status }: { status: IncidentStatus }) {
  const isActive = status === "analyzing" || status === "received";
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status]}`}>
      {isActive && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-400" />
        </span>
      )}
      {status}
    </span>
  );
}
