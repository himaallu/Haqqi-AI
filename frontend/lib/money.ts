/** Display only. Amounts come from the backend calculator as decimal strings and are never recomputed here. */
export function formatAed(amount: string): string {
  const [whole, fraction = ""] = amount.split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `AED ${grouped}.${fraction.padEnd(2, "0").slice(0, 2)}`;
}
