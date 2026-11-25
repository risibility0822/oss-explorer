import {createSourceTable, input, createEvaluator} from './runtime/cells.ts'
import {emitCompare} from './runtime/numeric-ui-core.ts'

const table = createSourceTable()
const cells = table.declare({n: input([1, 1000], {initial: 1, grid: 1})})
const circuit = table.createCircuit()
const c = v => circuit.constant(v)
// n % k === 0：先數 n 跨過幾個 k 的倍數，再算餘數
const divisible = k => {
  const bits = []
  for (let m = k; m <= 1000; m += k) bits.push([emitCompare(circuit, cells.n, '>=', c(m)), 1])
  const q = circuit.affine(bits); circuit.assumeRange(q, 0, Math.floor(1000 / k)); circuit.assumeGrid(q, 1)
  const r = circuit.affine([[cells.n, 1], [q, -k]]); circuit.assumeRange(r, 0, k - 1); circuit.assumeGrid(r, 1)
  return emitCompare(circuit, r, '===', c(0))
}
const d3 = divisible(3), d5 = divisible(5)
const fizzbuzz = circuit.reglu([], 1, [[d3, 1], [d5, 1]], -1)   // AND
const output = {fizzbuzz, fizz: circuit.affine([[d3, 1], [fizzbuzz, -1]])}
const built = {cells, output, ...table.finish()}
const evaluate = createEvaluator(built)

const src = new Float32Array(built.initialSource)
for (const n of [9, 15, 22]) {
  src[cells.n] = n
  console.log(n, evaluate(src).output)
}
