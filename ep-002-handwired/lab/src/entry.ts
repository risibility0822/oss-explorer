// 第 002 集瀏覽器 Demo：handwired 執行引擎 + FizzBuzz 數值程式
import {buildFizzBuzz, LABELS, MAX_N} from './fizzbuzz.ts'
import {perturbed} from './noise.ts'
const built: any = buildFizzBuzz()
const exact = built.circuit
let live = exact
let sigma = 0, seed = 1
const src = new Float32Array(built.initialSource)
const outWires = LABELS.map(l => built.output[l])
function run(n: number) {
  src[built.cells.n] = n
  const v = live.evaluateReference(src)
  const vals = outWires.map((w: number) => v[w])
  let best = 0; for (let i = 1; i < 4; i++) if (vals[i] > vals[best]) best = i
  const p = built.probe
  return {label: LABELS[best], vals, bits3: p.bits3.map((w: number) => v[w]), bits5: p.bits5.map((w: number) => v[w]), q3: v[p.q3], q5: v[p.q5], r3: v[p.r3], r5: v[p.r5]}
}
function setNoise(s: number, sd: number) { sigma = s; seed = sd; live = s === 0 ? exact : perturbed(exact, s, sd) }
const stats = (() => {
  let params = 0, relu = 0, affine = 0
  for (const op of exact.operations) { params += op.leftTerms.length + op.gateTerms.length + 2; if (op.kind === 'reglu') relu++; else affine++ }
  return {operations: exact.operations.length, reglu: relu, affine, params, depth: Math.max(...exact.operations.map((o: any) => o.depth))}
})()
;(globalThis as any).HW = {run, setNoise, stats, MAX_N, LABELS, get sigma() { return sigma }, get seed() { return seed }}
