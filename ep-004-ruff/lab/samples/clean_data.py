import re
import csv


def load(path):
    f = open(path, encoding="utf-8")
    rows = [r for r in csv.reader(f)]
    return rows


def clean(rows):
    seen = set()
    out = []
    for i in range(len(rows)):
        name = rows[i][0].strip()
        if not name in seen:
            seen.add(name)
            out.append(name)
    total = len(out)
    is_empty = lambda s: s == ""
    if type(out) == list:
        return [n for n in out if not is_empty(n)]
