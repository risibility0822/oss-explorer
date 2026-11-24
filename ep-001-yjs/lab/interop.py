from pycrdt import Doc, Text, Map
d = Doc(); d.apply_update(open('from_js.bin','rb').read())
t = d.get('note', type=Text); m = d.get('meta', type=Map)
print('Python 讀到:', str(t), dict(m))
with d.transaction(): t += '（Python 補充：記得帶筆電）'; m['rev'] = 2
open('from_py.bin','wb').write(d.get_update())
