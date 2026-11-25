import {buildFizzBuzz, referenceFizzBuzz, LABELS, MAX_N} from './fizzbuzz.ts'
import {createEvaluator} from './runtime/cells.ts'
const built = buildFizzBuzz()
const {circuit} = built
const evaluate = createEvaluator(built)
const src = new Float32Array(built.initialSource)
let ok = 0; const wrong: number[] = []
const t0 = performance.now()
for (let n = 1; n <= MAX_N; n++) {
  src[built.cells.n] = n
  const out = evaluate(src).output as any
  const vals = LABELS.map(l => out[l])
  const exact = vals.every(v => v === 0 || v === 1) && vals.reduce((a, b) => a + b, 0) === 1
  const label = LABELS[vals.indexOf(1)]
  if (exact && label === referenceFizzBuzz(n)) ok++; else wrong.push(n)
}
const ms = performance.now() - t0
const kinds: Record<string, number> = {}
for (const op of circuit.operations) kinds[op.kind] = (kinds[op.kind] ?? 0) + 1
const maxDepth = Math.max(...circuit.operations.map(o => o.depth))
let coeffs = 0
for (const op of circuit.operations) coeffs += op.leftTerms.length + op.gateTerms.length + 2
console.log(JSON.stringify({maxN: MAX_N, correct: ok, wrong, operations: circuit.operations.length, kinds, depth: maxDepth, parameters: coeffs, msFor1000: +ms.toFixed(2)}, null, 1))
