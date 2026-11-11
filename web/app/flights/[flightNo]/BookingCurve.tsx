type Point = { snapshot_date: string; seats_sold: number };

/** Seats sold per day (the snapshot the engine uses), with the aircraft capacity as a dashed line. */
export function BookingCurve({ snapshots, capacity }: { snapshots: Point[]; capacity: number }) {
  if (snapshots.length === 0) return <p className="sub">No booking data yet.</p>;
  const W = 1000, H = 300, L = 48, R = 24, T = 16, B = 36;
  const maxY = Math.max(capacity, ...snapshots.map((s) => s.seats_sold)) * 1.08;
  const x = (i: number) => L + (i * (W - L - R)) / Math.max(1, snapshots.length - 1);
  const y = (v: number) => T + (H - T - B) * (1 - v / maxY);
  const line = snapshots.map((s, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(s.seats_sold).toFixed(1)}`).join(" ");
  const area = `${line} L${x(snapshots.length - 1).toFixed(1)},${y(0)} L${x(0)},${y(0)} Z`;
  const ticks = [0, Math.round(capacity / 2), capacity];
  const last = snapshots[snapshots.length - 1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
      aria-label={`Booking curve: ${last.seats_sold} of ${capacity} seats sold on ${last.snapshot_date}`}>
      {ticks.map((t) => (
        <g key={t}>
          <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="#eaecf0" />
          <text x={L - 8} y={y(t) + 4} textAnchor="end" fontSize="12" fill="#667085">{t}</text>
        </g>
      ))}
      <line x1={L} x2={W - R} y1={y(capacity)} y2={y(capacity)} stroke="#98a2b3" strokeDasharray="5 4" />
      <text x={W - R} y={y(capacity) - 6} textAnchor="end" fontSize="12" fill="#667085">capacity {capacity}</text>
      <path d={area} fill="#2f5bea" opacity="0.08" />
      <path d={line} fill="none" stroke="#2f5bea" strokeWidth="2.5" />
      {snapshots.map((s, i) => (
        <circle key={s.snapshot_date} cx={x(i)} cy={y(s.seats_sold)} r={i === snapshots.length - 1 ? 4 : 2.5} fill="#2f5bea">
          <title>{`${s.snapshot_date}: ${s.seats_sold} seats`}</title>
        </circle>
      ))}
      <text x={x(snapshots.length - 1)} y={y(last.seats_sold) - 10} textAnchor="end" fontSize="13" fontWeight="600" fill="#1b2430">
        {last.seats_sold}
      </text>
      <text x={L} y={H - 10} fontSize="12" fill="#667085">{snapshots[0].snapshot_date}</text>
      <text x={W - R} y={H - 10} fontSize="12" fill="#667085" textAnchor="end">{last.snapshot_date}</text>
    </svg>
  );
}
