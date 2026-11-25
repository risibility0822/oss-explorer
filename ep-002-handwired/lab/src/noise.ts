// 把電路的權重「解凍」：每個係數與偏差乘上 (1 + σ·N(0,1))，看 FizzBuzz 還剩幾題對
import {LABELS} from './fizzbuzz.ts'
export function mulberry32(seed: number) {
  return () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}
export function gaussian(rand: () => number) { const u = 1 - rand(), v = rand(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v) }
export function perturbed(circuit: any, sigma: number, seed: number) {
  const rand = mulberry32(seed)
  const j = (x: number) => sigma === 0 ? x : x * (1 + sigma * gaussian(rand))
  const ops = circuit.operations.map((op: any) => ({...op,
    leftTerms: op.leftTerms.map(([w, k]: [number, number]) => [w, j(k)]), leftBias: j(op.leftBias),
    gateTerms: op.gateTerms.map(([w, k]: [number, number]) => [w, j(k)]), gateBias: j(op.gateBias)}))
  const clone = Object.create(circuit); clone.operations = ops
  return clone
}
// 回傳 1..maxN 每一題的預測（0..3 = number/fizz/buzz/fizzbuzz，取最大值）
export function predictAll(circuit: any, built: any, maxN: number) {
  const src = new Float32Array(built.initialSource)
  const wires = LABELS.map(l => built.output[l])
  const preds = new Uint8Array(maxN + 1)
  for (let n = 1; n <= maxN; n++) {
    src[built.cells.n] = n
    const v = circuit.evaluateReference(src)
    let best = 0; for (let i = 1; i < 4; i++) if (v[wires[i]] > v[wires[best]]) best = i
    preds[n] = best
  }
  return preds
}
