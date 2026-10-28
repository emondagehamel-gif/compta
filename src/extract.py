import re, sys
src = open('Comptabilite/Comptabilite.html', encoding='utf-8').read()
js = src[src.index('<script>')+8:src.rindex('</script>')]
lines = js.split('\n')
# découper en blocs de niveau supérieur (lignes en colonne 0)
chunks, cur = [], []
for ln in lines:
    if ln and not ln[0].isspace() and not ln[0] in '})]' and cur:
        chunks.append(cur); cur = []
    cur.append(ln)
if cur: chunks.append(cur)
def names(chunk):
    first = chunk[0]
    m = re.match(r'(?:async\s+)?function\s+([\w$]+)\s*\(', first)
    if m: return [m.group(1)]
    m = re.match(r'(?:const|let|var)\s+(.*)', first)
    if m:
        # noms déclarés au niveau supérieur de la ligne : "A = ..., B = ..."
        decl = m.group(1); out = []; depth = 0; tok = ''
        parts = []; buf = ''
        for ch in decl:
            if ch in '([{': depth += 1
            elif ch in ')]}': depth -= 1
            if ch == ',' and depth == 0: parts.append(buf); buf = ''
            else: buf += ch
        parts.append(buf)
        for p in parts:
            mm = re.match(r'\s*([\w$]+)\s*=', p)
            if mm: out.append(mm.group(1))
        return out
    return []
want = sys.argv[1].split(',')
found, out = set(), []
for ch in chunks:
    ns = names(ch)
    if any(n in want for n in ns):
        out.append('\n'.join(ch).rstrip()); found.update(n for n in ns if n in want)
missing = [w for w in want if w not in found]
if missing: print('MISSING:', missing, file=sys.stderr); sys.exit(1)
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('ok', len(out), 'blocs')
