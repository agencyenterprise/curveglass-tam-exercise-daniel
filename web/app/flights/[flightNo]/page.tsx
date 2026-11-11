import { api } from "@/lib/api";
import { formatChange, formatMoney, formatPct, loadFactor } from "@/lib/metrics";
import { BookingCurve } from "./BookingCurve";

export default async function FlightPage({ params }: { params: { flightNo: string } }) {
  const { flight, snapshots, recommendations } = await api.flight(params.flightNo);
  const latest = snapshots.at(-1);
  return (
    <>
      <h1>{flight.flight_no} · {flight.segment}</h1>
      <p className="sub">Departs {flight.dep_date} {flight.dep_time_local} · {flight.equipment || "equipment unknown"}</p>

      <div className="stats">
        <div className="card stat"><div className="label">Capacity</div><div className="value">{flight.capacity}</div></div>
        <div className="card stat"><div className="label">Seats sold</div><div className="value">{latest?.seats_sold ?? "—"}</div></div>
        <div className="card stat"><div className="label">Load factor</div>
          <div className="value">{latest ? formatPct(loadFactor(latest.seats_sold, flight.capacity)) : "—"}</div></div>
        <div className="card stat"><div className="label">Latest snapshot</div><div className="value">{latest?.snapshot_date.slice(5) ?? "—"}</div></div>
      </div>

      <h2>Booking curve</h2>
      <div className="card"><BookingCurve snapshots={snapshots} capacity={flight.capacity} /></div>

      <h2>Recommendations</h2>
      <table>
        <thead><tr><th>Run</th><th>Reason</th><th className="num">Price change</th><th>Guardrail</th>
          <th className="num">LF at run</th><th>Status</th></tr></thead>
        <tbody>
          {recommendations.map((r) => (
            <tr key={r.run_id}>
              <td>{r.run_id}</td><td>{r.model_code}</td>
              <td className={`num ${r.raw_offer_value > 0 ? "up" : "down"}`}>{formatChange(r.raw_offer_value)}</td>
              <td>{r.guardrail_applied}</td>
              <td className="num">{formatPct(r.lf_at_run)}</td>
              <td><span className={`pill ${r.status}`}>{r.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Bookings by day</h2>
      <table>
        <thead><tr><th>Snapshot</th><th className="num">Seats sold</th><th className="num">Avg fare</th></tr></thead>
        <tbody>
          {[...snapshots].reverse().slice(0, 10).map((s) => (
            <tr key={s.snapshot_date}>
              <td>{s.snapshot_date}</td><td className="num">{s.seats_sold}</td><td className="num">{formatMoney(s.avg_fare)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
