export function categoryHue(name: string): number {
  let h = 0;
  for (const ch of name) {
    h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  }
  return Math.round(((h * 0.6180339887) % 1) * 360);
}