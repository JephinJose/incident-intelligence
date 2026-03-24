import axios from "axios";

export const api = axios.create({ baseURL: "/api/v1" });

export const incidentsApi = {
  list: (params?: Record<string, string | number>) =>
    api.get("/incidents", { params }).then((r) => r.data),
  get: (id: number) => api.get(`/incidents/${id}`).then((r) => r.data),
  stats: () => api.get("/incidents/stats").then((r) => r.data),
  triggerAnalysis: (id: number) =>
    api.post(`/incidents/${id}/analyze`).then((r) => r.data),
  create: (payload: unknown) =>
    api.post("/incidents", payload).then((r) => r.data),
  getRunbook: (id: number) =>
    api.get(`/incidents/${id}/runbook`).then((r) => r.data),
};
