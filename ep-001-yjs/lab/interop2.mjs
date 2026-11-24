import * as Y from 'yjs'; import fs from 'fs'
const d = new Y.Doc(); Y.applyUpdate(d, fs.readFileSync('from_py.bin'))
console.log('JS 讀回:', d.getText('note').toString(), d.getMap('meta').toJSON())
