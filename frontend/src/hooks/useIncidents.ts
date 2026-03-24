import { useQuery } from "@tanstack/react-query";
import { incidentsApi } from "../api/client";
import type { IncidentDetail, IncidentStats, IncidentSummary } from "../types";

export function useIncidents(filters?: Record<string, string | number>) {
  return useQuery<IncidentSummary[]>({
    queryKey: ["incidents", filters],
    queryFn: () => incidentsApi.list(filters),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.some((i: IncidentSummary) => i.status === "analyzing" || i.status === "received"))
        return 4000;
      return false;
    },
  });
}

export function useIncident(id: number) {
  return useQuery<IncidentDetail>({
    queryKey: ["incident", id],
    queryFn: () => incidentsApi.get(id),
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "analyzing" || s === "received" ? 3000 : false;
    },
  });
}

export function useIncidentStats() {
  return useQuery<IncidentStats>({
    queryKey: ["incident-stats"],
    queryFn: incidentsApi.stats,
    refetchInterval: 15_000,
  });
}
