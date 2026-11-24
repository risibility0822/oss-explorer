import * as Y from 'yjs'; import fs from 'fs'
const d = new Y.Doc(); d.getText('note').insert(0,'JS 寫的筆記：明天 10 點開會')
const m = d.getMap('meta'); m.set('author','JS 端'); m.set('rev',1)
fs.writeFileSync('from_js.bin', Y.encodeStateAsUpdate(d))
