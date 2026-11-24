import * as Y from 'yjs'
const d=new Y.Doc(),t=d.getText('t'); const s='開源探索誌'.repeat(2000)
for(let i=0;i<s.length;i++) t.insert(i,s[i])
console.log(JSON.stringify({chars:t.length,bytesV1:Y.encodeStateAsUpdate(d).length,bytesV2:Y.encodeStateAsUpdateV2(d).length,utf8:Buffer.byteLength(s)}))
