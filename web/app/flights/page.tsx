import Link from "next/link";
import { api } from "@/lib/api";
import { formatPct, loadFactor } from "@/lib/metrics";

export default async function FlightsPage({ searchParams }: { searchParams: { airline?: string; search?: string } }) {
  const airline = searchParams.airline ?? "";
  const flights = await api.flights({ airline, search: searchParams.search });
  return (
    <>
      <h1>Flights</h1>
      <form className="filters">
        <select name="airline" defaultValue={airline}>
          <option value="">All airlines</option>
          <option value="ZZ">ZZ</option>
          <option value="SR">SR</option>
        </select>
        <input name="search" placeholder="Flight or segment" defaultValue={searchParams.search ?? ""} />
        <button type="submit">Filter</button>
      </form>
      <p className="sub">{flights.length} flights</p>
      <table>
        <thead>
          <tr><th>Flight</th><th>Segment</th><th>Departure</th><th>Equipment</th>
            <th className="num">Capacity</th><th className="num">Seats sold</th><th className="num">Load factor</th></tr>
        </thead>
        <tbody>
          {flights.map((f) => (
            <tr key={f.flight_id}>
              <td><Link href={`/flights/${f.flight_no}`}>{f.flight_no}</Link></td>
              <td>{f.segment}</td>
              <td>{f.dep_date} {f.dep_time_local}</td>
              <td>{f.equipment || "—"}</td>
              <td className="num">{f.capacity}</td>
              <td className="num">{f.seats_sold ?? "—"}</td>
              <td className="num">{f.seats_sold == null ? "—" : formatPct(loadFactor(f.seats_sold, f.capacity))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
