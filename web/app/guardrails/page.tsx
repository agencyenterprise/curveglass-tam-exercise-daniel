import { api, ApiError } from "@/lib/api";
import { formatPct } from "@/lib/metrics";
import { NoAccess } from "../NoAccess";

export default async function GuardrailsPage() {
  let g;
  try {
    g = await api.guardrails();
  } catch (e) {
    if (e instanceof ApiError && e.status === 403) return <NoAccess what="guardrails" />;
    throw e;
  }
  return (
    <>
      <h1>Guardrails · {g.airline}</h1>
      <p className="sub">Config v{g.version}, last changed {g.updated_at.slice(0, 10)} by {g.updated_by}</p>
      <table>
        <tbody>
          <tr><th>Hard cap on any price change</th><td>±{formatPct(g.pct_hard_cap)}</td></tr>
          <tr><th>Auto-approval</th><td>{g.auto_approve.enabled ? "On" : "Off"} for {g.auto_approve.segments.join(", ")}</td></tr>
          <tr><th>Auto-approval limit</th><td>±{formatPct(g.auto_approve.max_abs_change)}</td></tr>
          <tr><th>Blackout dates (no changes)</th><td>{g.blackout_dates.join(", ")}</td></tr>
        </tbody>
      </table>
    </>
  );
}
