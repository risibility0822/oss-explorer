import { Server } from '@hocuspocus/server'
import { HocuspocusProvider } from '@hocuspocus/provider'
import * as Y from 'yjs'
import WebSocket from 'ws'
globalThis.WebSocket = WebSocket
const server = new Server({ port: 1234, quiet: true })
await server.listen()
const mk = (name) => { const doc = new Y.Doc(); const p = new HocuspocusProvider({ url: 'ws://127.0.0.1:1234', name: 'demo-room', document: doc }); return { doc, p } }
const a = mk('a'), b = mk('b')
await new Promise(r => setTimeout(r, 800))
a.doc.getText('t').insert(0, 'Hello from A')
b.doc.getMap('m').set('fromB', '嗨，我是 B')
await new Promise(r => setTimeout(r, 800))
console.log('A sees:', a.doc.getText('t').toString(), a.doc.getMap('m').toJSON())
console.log('B sees:', b.doc.getText('t').toString(), b.doc.getMap('m').toJSON())
a.p.destroy(); b.p.destroy(); await server.destroy(); process.exit(0)
