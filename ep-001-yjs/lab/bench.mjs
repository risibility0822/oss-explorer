// Real benchmark run in the workspace: offline edits on two replicas, then merge.
import * as Y from 'yjs'

const now = () => Number(process.hrtime.bigint()) / 1e6
const out = { node: process.version, yjs: '13.6.33', runs: [] }

// --- Scenario 1: two people edit the same text offline, then reconnect ---
function scenarioText(editsEach) {
  const base = new Y.Doc()
  base.getText('t').insert(0, '今天的會議記錄：')
  const seed = Y.encodeStateAsUpdate(base)
  const a = new Y.Doc(); a.clientID = 1; Y.applyUpdate(a, seed)
  const b = new Y.Doc(); b.clientID = 2; Y.applyUpdate(b, seed)
  const ta = a.getText('t'), tb = b.getText('t')
  const t0 = now()
  for (let i = 0; i < editsEach; i++) {
    ta.insert(Math.floor(ta.length * ((i * 7919) % 100) / 100), 'A')
    tb.insert(Math.floor(tb.length * ((i * 104729) % 100) / 100), 'B')
    if (i % 5 === 4) { ta.delete(Math.max(0, ta.length - 3), 1); tb.delete(0, 1) }
  }
  const t1 = now()
  const svA = Y.encodeStateVector(a), svB = Y.encodeStateVector(b)
  const diffAtoB = Y.encodeStateAsUpdate(a, svB)
  const diffBtoA = Y.encodeStateAsUpdate(b, svA)
  const t2 = now()
  Y.applyUpdate(b, diffAtoB); Y.applyUpdate(a, diffBtoA)
  const t3 = now()
  return {
    scenario: 'text', editsEach,
    editMs: +(t1 - t0).toFixed(1), mergeMs: +(t3 - t2).toFixed(2),
    syncBytes: diffAtoB.length + diffBtoA.length,
    finalLength: ta.length, converged: ta.toString() === tb.toString(),
    docBytes: Y.encodeStateAsUpdate(a).length,
    docBytesV2: Y.encodeStateAsUpdateV2(a).length,
  }
}

// --- Scenario 2: a shared to-do list (Y.Array of Y.Map), concurrent ops ---
function scenarioTodo() {
  const a = new Y.Doc(); a.clientID = 1
  const b = new Y.Doc(); b.clientID = 2
  const la = a.getArray('todos')
  for (const t of ['買牛奶', '寫週報', '修 bug #42']) { const m = new Y.Map(); m.set('t', t); m.set('done', false); la.push([m]) }
  Y.applyUpdate(b, Y.encodeStateAsUpdate(a))
  const lb = b.getArray('todos')
  // offline: A checks item 0 and renames item 2; B deletes item 1 and adds one
  la.get(0).set('done', true); la.get(2).set('t', '修 bug #42（急）')
  lb.delete(1, 1); const m = new Y.Map(); m.set('t', '訂機票'); m.set('done', false); lb.push([m])
  Y.applyUpdate(a, Y.encodeStateAsUpdate(b, Y.encodeStateVector(a)))
  Y.applyUpdate(b, Y.encodeStateAsUpdate(a, Y.encodeStateVector(b)))
  const view = d => d.getArray('todos').toArray().map(x => (x.get('done') ? '☑ ' : '☐ ') + x.get('t'))
  return { scenario: 'todo', a: view(a), b: view(b), converged: JSON.stringify(view(a)) === JSON.stringify(view(b)) }
}

// --- Scenario 3: naive "last write wins" JSON for comparison ---
function naiveLWW() {
  const server = { todos: ['買牛奶', '寫週報', '修 bug #42'] }
  const a = structuredClone(server), b = structuredClone(server)
  a.todos[0] = '☑ 買牛奶'; a.todos[2] = '修 bug #42（急）'
  b.todos.splice(1, 1); b.todos.push('訂機票')
  const result = Object.assign({}, server, a, b) // b saved last → overwrites a
  return { scenario: 'naive-lww', result: result.todos, lostEdits: ['☑ 買牛奶', '修 bug #42（急）'].filter(x => !result.todos.includes(x)) }
}

for (const n of [100, 1000, 10000]) out.runs.push(scenarioText(n))
out.runs.push(scenarioTodo())
out.runs.push(naiveLWW())
console.log(JSON.stringify(out, null, 1))
