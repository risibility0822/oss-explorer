import {buildFizzBuzz, referenceFizzBuzz, LABELS} from './fizzbuzz.ts'
import {perturbed, predictAll} from './noise.ts'
const built = buildFizzBuzz()
const N = 100
const sigmas = [0, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.03, 0.1, 0.3]
const rows: any[] = []
for (const s of sigmas) {
  const accs: number[] = []
  for (let seed = 1; seed <= 10; seed++) {
    const p = predictAll(perturbed(built.circuit, s, seed), built, N)
    let ok = 0; for (let n = 1; n <= N; n++) if (LABELS[p[n]] === referenceFizzBuzz(n)) ok++
    accs.push(ok)
  }
  rows.push({sigma: s, correctOutOf100_10seeds: accs, mean: accs.reduce((a, b) => a + b) / accs.length})
}
console.log(JSON.stringify(rows, null, 1))
