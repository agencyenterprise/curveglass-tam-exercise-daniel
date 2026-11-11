import Link from "next/link";
import { api } from "@/lib/api";

export default async function RunsPage() {
  const runs = await api.runs();
  return (
    <>
      <h1>Pricing runs · ZZ</h1>
      <p className="sub">Daily run at 06:00 local. Open a run to see its review queue.</p>
      <table>
        <thead>
          <tr><th>Run</th><th>Started (UTC)</th><th>Status</th>
            <th className="num">Flights with recs</th><th className="num">Recs written</th>
            <th className="num">Guardrail binds</th></tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.run_id}>
              <td><Link href={`/runs/${r.run_id}`}>{r.run_id}</Link></td>
              <td>{r.started_at.replace("T", " ").replace("Z", "")}</td>
              <td><span className="pill">{r.status}</span></td>
              <td className="num">{r.flights_with_recs}</td>
              <td className="num">{r.recs_written}</td>
              <td className="num">{r.guardrail_binds}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
