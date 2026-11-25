import {buildFizzBuzz, referenceFizzBuzz, LABELS} from './fizzbuzz.ts'
const built = buildFizzBuzz()
const wires = LABELS.map(l => (built.output as any)[l])
const ev = built.circuit.createTensorEvaluator(wires)
const src = new Float32Array(built.initialSource)
const R = 200
let sink = 0
for (let n = 1; n <= 1000; n++) { src[built.cells.n] = n; sink += ev(src)[1] } // warm up
let t0 = performance.now()
for (let r = 0; r < R; r++) for (let n = 1; n <= 1000; n++) { src[built.cells.n] = n; sink += ev(src)[1] }
const circuitNs = (performance.now() - t0) * 1e6 / (R * 1000)
t0 = performance.now()
let s2 = 0
for (let r = 0; r < R * 50; r++) for (let n = 1; n <= 1000; n++) s2 += referenceFizzBuzz(n).length
const jsNs = (performance.now() - t0) * 1e6 / (R * 50 * 1000)
console.log(JSON.stringify({node: process.version, circuitNsPerEval: +circuitNs.toFixed(1), plainJsNsPerEval: +jsNs.toFixed(2), ratio: Math.round(circuitNs / jsNs), sink: sink > 0, s2: s2 > 0}))
