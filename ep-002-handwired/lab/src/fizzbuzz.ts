// FizzBuzz 寫成 handwired 數值程式（只有加權和、ReLU 乘積、四捨五入成 0/1）
import {createSourceTable, input} from './runtime/cells.ts'
import {emitCompare, type Wire} from './runtime/numeric-ui-core.ts'

export const MAX_N = 1000

export function buildFizzBuzz(maxN = MAX_N) {
  const table = createSourceTable()
  const cells = table.declare({n: input([1, maxN], {initial: 1, grid: 1})})
  const circuit = table.createCircuit()
  const n = cells.n
  const c = (v: number) => circuit.constant(v)
  // JS: Math.floor(n / k) ＝ 數一數 n 跨過了幾個 k 的倍數（handwired 文件的 threshold count 寫法）
  const probe: Record<string, any> = {}
  const floorDiv = (k: number) => {
    const bits: [Wire, number][] = []
    for (let m = k; m <= maxN; m += k) bits.push([emitCompare(circuit, n, '>=', c(m)), 1])
    const q = circuit.affine(bits, 0)
    circuit.assumeRange(q, 0, Math.floor(maxN / k)); circuit.assumeGrid(q, 1)
    probe['bits' + k] = bits.map(b => b[0]); probe['q' + k] = q
    return q
  }
  // JS: n % k === 0
  const divisible = (k: number) => {
    const q = floorDiv(k)
    const r = circuit.affine([[n, 1], [q, -k]], 0)
    circuit.assumeRange(r, 0, k - 1); circuit.assumeGrid(r, 1)
    probe['r' + k] = r
    return emitCompare(circuit, r, '===', c(0))
  }
  const d3 = divisible(3)
  const d5 = divisible(5)
  // JS: d3 && d5
  const fizzbuzz = circuit.reglu([], 1, [[d3, 1], [d5, 1]], -1)
  const fizz = circuit.affine([[d3, 1], [fizzbuzz, -1]])
  const buzz = circuit.affine([[d5, 1], [fizzbuzz, -1]])
  const number = circuit.affine([[d3, -1], [d5, -1], [fizzbuzz, 1]], 1)
  const output = {number, fizz, buzz, fizzbuzz}
  return {cells, output, probe, ...table.finish()}
}

export const LABELS = ['number', 'fizz', 'buzz', 'fizzbuzz'] as const
export function referenceFizzBuzz(n: number) {
  if (n % 15 === 0) return 'fizzbuzz'
  if (n % 3 === 0) return 'fizz'
  if (n % 5 === 0) return 'buzz'
  return 'number'
}
