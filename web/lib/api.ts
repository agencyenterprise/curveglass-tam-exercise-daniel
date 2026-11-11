// Server-side client for the FastAPI service (api/main.py).
// The logged-in user is kept in the "user" cookie and sent to the API as X-User.
import { cookies } from "next/headers";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export type Me = { id: string; name: string; role: string; permissions: string[] };
export type User = { id: string; name: string; role: string };
export type Run = {
  run_id: string; started_at: string; finished_at: string; status: string;
  flights_with_recs: number; recs_written: number; guardrail_binds: number;
};
export type QueueItem = {
  flight_no: string; segment: string; dep_date: string; model_code: string;
  raw_offer_value: number; offer_value: number; guardrail_applied: string; status: string;
};
export type FlightRow = {
  flight_id: number; airline: string; flight_no: string; segment: string; market: string;
  dep_date: string; dep_time_local: string; equipment: string; capacity: number;
  snapshot_date: string | null; seats_sold: number | null;
};
export type FlightDetail = {
  flight: FlightRow;
  snapshots: { snapshot_date: string; seats_sold: number; avg_fare: number }[];
  recommendations: {
    run_id: string; model_code: string; raw_offer_value: number; offer_value: number; guardrail_applied: string;
    status: string; seats_sold_at_run: number; lf_at_run: number;
  }[];
  publications: { run_id: string; price_change: number; sent_at: string }[];
};
export type Guardrails = {
  airline: string; version: number; updated_at: string; updated_by: string; pct_hard_cap: number;
  auto_approve: { enabled: boolean; segments: string[]; max_abs_change: number };
  blackout_dates: string[];
};

export function currentUserId(): string | undefined {
  return cookies().get("user")?.value;
}

async function get<T>(path: string): Promise<T> {
  const user = currentUserId();
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers: user ? { "X-User": user } : {},
  });
  if (!res.ok) throw new ApiError(res.status, `${path} -> ${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  me: () => get<Me>("/api/me"),
  users: () => get<User[]>("/api/users"),
  runs: () => get<Run[]>("/api/runs"),
  queue: (runId: string, status?: string) =>
    get<QueueItem[]>(`/api/runs/${runId}/recommendations${status ? `?status=${status}` : ""}`),
  flights: (params: { airline?: string; search?: string }) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]);
    return get<FlightRow[]>(`/api/flights?${qs}`);
  },
  flight: (flightNo: string) => get<FlightDetail>(`/api/flights/${flightNo}`),
  guardrails: () => get<Guardrails>("/api/guardrails"),
};
