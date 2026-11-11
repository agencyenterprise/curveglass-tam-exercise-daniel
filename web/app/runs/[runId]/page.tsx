import Link from "next/link";
import { api } from "@/lib/api";
import { formatChange } from "@/lib/metrics";

const STATUSES = [
  { key: "", label: "All" },
  { key: "pending_review", label: "Pending review" },
  { key: "published", label: "Published" },
];

export default async function QueuePage({
  params, searchParams,
}: { params: { runId: string }; searchParams: { status?: string } }) {
  const status = searchParams.status ?? "";
  const items = await api.queue(params.runId, status || undefined);
  return (
    <>
      <h1>Review queue · {params.runId}</h1>
      <p className="sub">One recommendation per flight. Published = already sent to the airline&apos;s system.</p>
      <div className="filters">
        {STATUSES.map((s) => (
          <Link key={s.key} href={s.key ? `?status=${s.key}` : "?"} className={s.key === status ? "active" : ""}>
            {s.label}
          </Link>
        ))}
      </div>
      <table>
        <thead>
          <tr><th>Flight</th><th>Segment</th><th>Departure</th><th>Reason</th>
            <th className="num">Price change</th><th>Guardrail</th><th>Status</th></tr>
        </thead>
        <tbody>
          {items.map((r) => {
            const change = r.raw_offer_value;
            return (
              <tr key={r.flight_no}>
                <td><Link href={`/flights/${r.flight_no}`}>{r.flight_no}</Link></td>
                <td>{r.segment}</td>
                <td>{r.dep_date}</td>
                <td>{r.model_code}</td>
                <td className={`num ${change > 0 ? "up" : "down"}`}>{formatChange(change)}</td>
                <td>{r.guardrail_applied}</td>
                <td><span className={`pill ${r.status}`}>{r.status}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </>
  );
}
