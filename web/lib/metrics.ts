/** Load factor = seats sold / capacity, as a fraction (0.71 = 71%). */
export function loadFactor(seatsSold: number, capacity: number): number {
  return capacity > 0 ? seatsSold / capacity : 0;
}

/** Price changes are signed fractions: 0.18 -> "+18%", -0.05 -> "-5%". */
export function formatChange(value: number): string {
  const pct = Math.round(value * 100);
  return `${pct > 0 ? "+" : ""}${pct}%`;
}

export function formatPct(fraction: number): string {
  return `${Math.round(fraction * 100)}%`;
}

export function formatMoney(amount: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}
