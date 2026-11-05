#!/usr/bin/env python3
# Solance House — Copyright (c) 2026 House of Solance. All rights reserved. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
# Copyright (c) 2026 House of Solance. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
"""vault-map — a pure-local Obsidian vault index. Query the map, don't re-read the vault.

Built on the ideas of Graphify (https://github.com/Graphify-Labs/graphify): map a
corpus once, then answer orientation questions from the cheap map instead of
re-reading the corpus. Graphify's markdown path sends file contents to an LLM API;
a private vault must never leave the machine. So this reimplements the idea for
markdown vaults with zero deps, zero network, zero AI — the graph is already IN
the markdown (wikilinks, headings, tags, frontmatter). We just read it.
No Graphify code is used; original implementation, built 2026-07-19.

Usage:
  python3 vault-map.py build [vault_dir]
  python3 vault-map.py query "term term ..." [vault_dir] [--n 8] [--json] [--sections]
  python3 vault-map.py graph [vault_dir] [--out file.html]
  python3 vault-map.py path "note a" "note b" [vault_dir]

Map is stored at <vault_dir>/.vault-map.json (derived data, rebuild anytime, seconds).
`graph` writes a self-contained interactive vault-map-graph.html (zero network —
open it in any browser). `path` prints the shortest wikilink chain between two notes.
Default vault: $VAULT_MAP_DIR if set, else the current directory.
"""

import json, os, re, sys, time

DEFAULT_VAULT = os.environ.get("VAULT_MAP_DIR") or os.getcwd()
SKIP_DIRS = {".obsidian", "__pycache__", ".git", "node_modules", ".trash"}

FM_TAGS = re.compile(r"^tags:\s*\[?([^\]\n]+)\]?", re.M)
HEADING = re.compile(r"^(#{1,4})\s+(.+)$", re.M)
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
TAG = re.compile(r"(?:^|\s)#([A-Za-z][\w/-]{1,40})")

def norm(name):
    return name.strip().lower().replace(".md", "")

def build(vault):
    notes = {}
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, vault)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            heads = [h[1].strip() for h in HEADING.findall(text)]
            links = [norm(l) for l in WIKILINK.findall(text)]
            tags = set(t.lower() for t in TAG.findall(text))
            # Frontmatter: parse the whole block (they run long — files lists), and
            # accept tags on the same line OR bracket-list on the following line
            # (the session exporter's format). Also harvest type: and projects: —
            # they're tags in spirit, just a different dialect.
            if text.startswith("---"):
                end = text.find("\n---", 3, 8000)
                fmblock = text[3:end] if end > 0 else text[3:2000]
                m = re.search(r"^tags:\s*\n?\s*\[([^\]]+)\]", fmblock, re.M)
                if not m:
                    m = FM_TAGS.search(fmblock)
                if m:
                    tags |= {t.strip().strip("'\"").lower() for t in m.group(1).split(",") if t.strip()}
                t2 = re.search(r"^type:\s*(\S+)", fmblock, re.M)
                if t2:
                    tags.add(t2.group(1).lower())
                pm = re.search(r"^projects:\s*\n((?:\s+-\s+.+\n?)+)", fmblock, re.M)
                if pm:
                    for line in pm.group(1).splitlines():
                        p = line.strip().lstrip("-").strip().strip("'\"").lower()
                        if p and p != "[]":
                            tags.add(p)
                            if "/" in p:
                                tags.add(p.rsplit("/", 1)[-1])
            notes[norm(f)] = {
                "rel": rel,
                "title": heads[0] if heads else f[:-3],
                "headings": heads[:20],
                "links": links,
                "tags": sorted(tags)[:20],
                "bytes": len(text),
                "mtime": int(os.path.getmtime(path)),
            }
    # backlinks
    for name, n in notes.items():
        n["backlinks"] = []
    for name, n in notes.items():
        for target in n["links"]:
            if target in notes:
                notes[target]["backlinks"].append(name)
    out = {"built": int(time.time()), "vault": vault, "count": len(notes), "notes": notes}
    with open(os.path.join(vault, ".vault-map.json"), "w") as f:
        json.dump(out, f)
    print(f"vault-map: {len(notes)} notes indexed -> {os.path.join(vault, '.vault-map.json')}")

def search(terms, vault, top_n=8):
    """Rank notes against `terms`. Returns a dict, prints nothing — this is the
    importable/scriptable entry point; `query()` below is the human printer over it.
    Returns None when no map exists (run `build` first).

    Keeping compute and presentation separate means a caller embedding vault-map in
    a larger system reuses the ranking instead of reimplementing it and drifting."""
    path = os.path.join(vault, ".vault-map.json")
    if not os.path.exists(path):
        return None
    data = json.load(open(path))
    notes = data["notes"]
    terms = [t.lower() for t in terms if t.strip()]
    scored = []
    for name, n in notes.items():
        hay_title = (n["title"] + " " + name).lower()
        hay_heads = " ".join(n["headings"]).lower()
        hay_tags = " ".join(n["tags"])
        score = 0
        for t in terms:
            if t in hay_title: score += 5
            if t in hay_heads: score += 2
            if t in hay_tags: score += 3
            if t in n["rel"].lower(): score += 1
        # body scan — the transcripts' titles are generic; their bodies are the content.
        # Local read, ~1s across the whole vault; capped so one fat file can't dominate.
        snippet = ""
        try:
            body = open(os.path.join(vault, n["rel"]), encoding="utf-8", errors="replace").read().lower()
            for t in terms:
                hits = body.count(t)
                if hits:
                    score += min(hits, 10)
                    if not snippet:
                        i = body.find(t)
                        snippet = body[max(0, i - 60):i + 90].replace("\n", " ").strip()
        except OSError:
            pass
        if score:
            scored.append((score, name, n, snippet))
    scored.sort(key=lambda x: (-x[0], -x[2]["mtime"]))
    return {
        "query": " ".join(terms),
        "hits": len(scored),
        "map_age_days": round((time.time() - data["built"]) / 86400, 1),
        "results": [
            {
                "path": n["rel"],
                "title": n["title"],
                "score": score,
                "bytes": n["bytes"],
                "modified": time.strftime("%Y-%m-%d", time.localtime(n["mtime"])),
                "sections": n["headings"][1:4],
                "snippet": snippet,
                "links": n["links"][:5],
                "backlinks": n["backlinks"][:5],
            }
            for score, name, n, snippet in scored[:top_n]
        ],
    }


def query(terms, vault, top_n=8, as_json=False, sections=False):
    if sections:
        return query_sections(terms, vault, top_n, as_json)
    res = search(terms, vault, top_n)
    if res is None:
        print(json.dumps({"error": "no map — run build first"}) if as_json else "no map — run build first")
        return
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return
    if not res["results"]:
        print(f"no notes match: {res['query']}"); return
    print(f"vault-map query '{res['query']}' — {res['hits']} hits, "
          f"top {len(res['results'])} (map {res['map_age_days']}d old):")
    for r in res["results"]:
        links = ", ".join(r["links"]) or "-"
        backs = ", ".join(r["backlinks"]) or "-"
        heads = " | ".join(r["sections"])
        print(f"\n[{r['score']}] {r['path']}  ({r['bytes']//1000}k, {r['modified']})")
        print(f"    title: {r['title']}")
        if heads: print(f"    sections: {heads}")
        if r["snippet"]: print(f"    ...{r['snippet']}...")
        print(f"    links-> {links}   <-backlinks {backs}")

def _load_map(vault):
    p = os.path.join(vault, ".vault-map.json")
    if not os.path.exists(p):
        print("no map — run build first"); sys.exit(1)
    return json.load(open(p))

def _adjacency(notes):
    adj = {name: set() for name in notes}
    for name, n in notes.items():
        for t in n["links"]:
            if t in notes and t != name:
                adj[name].add(t); adj[t].add(name)
    return adj

def _resolve(q, notes):
    q = q.lower().strip()
    if q in notes:
        return q
    hits = [n for n in notes if q in n] or \
           [n for n, d in notes.items() if q in d["title"].lower()]
    if not hits:
        print(f"no note matches: {q}"); sys.exit(1)
    hits.sort(key=lambda n: (len(n), n))
    if len(hits) > 1:
        print(f"({len(hits)} notes match '{q}' — using '{hits[0]}')")
    return hits[0]

def path_cmd(qa, qb, vault):
    notes = _load_map(vault)["notes"]
    a, b = _resolve(qa, notes), _resolve(qb, notes)
    adj = _adjacency(notes)
    prev, seen, frontier = {}, {a}, [a]
    while frontier and b not in prev and b != a:
        nxt = []
        for u in frontier:
            for v in adj[u]:
                if v not in seen:
                    seen.add(v); prev[v] = u; nxt.append(v)
        frontier = nxt
    if b != a and b not in prev:
        print(f"no wikilink path between '{a}' and '{b}' (different islands)"); return
    chain = [b]
    while chain[-1] != a:
        chain.append(prev[chain[-1]])
    chain.reverse()
    print(f"shortest path ({len(chain) - 1} hop{'s' if len(chain) != 2 else ''}):")
    for i, name in enumerate(chain):
        pad = "  " * i + ("" if i == 0 else "→ ")
        print(f"  {pad}{notes[name]['title']}  ({notes[name]['rel']})")

# Categorical folder palette, dark surface — validated (lightness band, chroma,
# CVD ΔE, normal-vision floor, contrast) with the dataviz six-checks script.
GRAPH_PALETTE = ["#3D8CD9", "#C98300", "#009E73", "#9B7FE8", "#C0392B", "#C4699C"]
GRAPH_OTHER = "#8A8F98"

def graph_cmd(vault, out=None):
    data = _load_map(vault)
    notes = data["notes"]
    names = list(notes)
    idx = {n: i for i, n in enumerate(names)}
    folders = {}
    for n in names:
        f = notes[n]["rel"].split(os.sep)[0] if os.sep in notes[n]["rel"] else "(root)"
        folders[f] = folders.get(f, 0) + 1
    ranked = sorted(folders, key=lambda f: -folders[f])
    top = ranked[:len(GRAPH_PALETTE)]
    fnames = top + (["other"] if len(ranked) > len(top) else [])
    fidx = {f: i for i, f in enumerate(top)}
    edges = set()
    for n in names:
        for t in notes[n]["links"]:
            if t in idx and t != n:
                edges.add((min(idx[n], idx[t]), max(idx[n], idx[t])))
    N = []
    for n in names:
        d = notes[n]
        f = d["rel"].split(os.sep)[0] if os.sep in d["rel"] else "(root)"
        N.append([d["title"], d["rel"], fidx.get(f, len(top)),
                  len(d["backlinks"]), len(d["links"])])
    payload = {"n": N, "e": sorted(edges), "f": fnames,
               "c": GRAPH_PALETTE[:len(top)] + ([GRAPH_OTHER] if len(fnames) > len(top) else []),
               "built": data["built"], "count": data["count"]}
    # escape "</" so a hostile note title can't close the <script> block (XSS)
    blob = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    html = GRAPH_TEMPLATE.replace("__DATA__", blob)
    out = out or os.path.join(vault, "vault-map-graph.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"vault-map graph: {len(N)} notes, {len(edges)} links -> {out}")
    print("open it in any browser (double-click, or: open '" + out + "')")

GRAPH_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>vault-map graph</title>
<link rel="icon" href="data:,">
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#1a1a19;
    font:13px/1.4 system-ui,-apple-system,sans-serif;color:#d7dae0}
  canvas{display:block;cursor:grab}
  #top{position:fixed;top:12px;left:14px;right:14px;display:flex;gap:14px;
    align-items:flex-start;pointer-events:none;flex-wrap:wrap}
  #search{pointer-events:auto;background:#24262b;border:1px solid #3a3d44;color:#d7dae0;
    border-radius:6px;padding:7px 11px;width:240px;font:inherit;outline:none}
  #search:focus{border-color:#3D8CD9}
  #legend{pointer-events:auto;display:flex;gap:10px 14px;flex-wrap:wrap;align-items:center;
    background:rgba(26,26,25,.82);border-radius:6px;padding:7px 10px;max-width:60vw}
  .chip{display:flex;gap:6px;align-items:center;color:#9aa0a8;cursor:pointer;user-select:none}
  .chip.off{opacity:.35}
  .dot{width:9px;height:9px;border-radius:50%}
  #tip{position:fixed;display:none;background:#24262b;border:1px solid #3a3d44;border-radius:6px;
    padding:8px 11px;pointer-events:none;max-width:320px;z-index:3}
  #tip b{color:#fff;font-weight:600}
  #tip .m{color:#9aa0a8;font-size:12px;margin-top:3px}
  #stats{position:fixed;left:14px;bottom:12px;color:#9aa0a8;font-size:12px}
  #hint{position:fixed;right:14px;bottom:12px;color:#6d727b;font-size:12px;text-align:right}
</style></head><body>
<canvas id="cv"></canvas>
<div id="top"><input id="search" placeholder="find a note… (Enter jumps)" spellcheck="false">
<div id="legend"></div></div>
<div id="tip"></div><div id="stats"></div>
<div id="hint">drag&nbsp;pan &middot; scroll&nbsp;zoom &middot; hover/click&nbsp;a&nbsp;note &middot; drag&nbsp;a&nbsp;node</div>
<script>
const D=__DATA__;
const cv=document.getElementById('cv'),cx=cv.getContext('2d');
const tip=document.getElementById('tip'),stats=document.getElementById('stats');
const n=D.n.length,X=new Float64Array(n),Y=new Float64Array(n),
      VX=new Float64Array(n),VY=new Float64Array(n),R=new Float64Array(n);
const deg=new Int32Array(n),adj=Array.from({length:n},()=>[]);
for(const[a,b]of D.e){adj[a].push(b);adj[b].push(a);deg[a]++;deg[b]++}
for(let i=0;i<n;i++){R[i]=2.5+Math.min(9,Math.sqrt(D.n[i][3]+D.n[i][4])*1.1);
  const t=i*2.399963,r=14*Math.sqrt(i);X[i]=Math.cos(t)*r;Y[i]=Math.sin(t)*r}
const folderOn=D.f.map(()=>true);
let W,H,dpr,tx=0,ty=0,sc=1,alpha=1,hover=-1,sel=-1,dragN=-1,panning=false,
    px=0,py=0,dirty=true,nbrs=new Set(),origin=false,moveDist=0;
function resize(){dpr=devicePixelRatio||1;W=innerWidth;H=innerHeight;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.width=W+'px';cv.style.height=H+'px';
  if(!origin){tx=W/2;ty=H/2;origin=true}dirty=true}
addEventListener('resize',resize);resize();
function tick(){ // grid-bucketed repulsion + edge springs + center gravity
  const cell=60,grid=new Map();
  for(let i=0;i<n;i++){const k=((X[i]/cell)|0)+':'+((Y[i]/cell)|0);
    (grid.get(k)||grid.set(k,[]).get(k)).push(i)}
  const kr=1400*alpha;
  for(let i=0;i<n;i++){const gx=(X[i]/cell)|0,gy=(Y[i]/cell)|0;
    for(let ox=-1;ox<2;ox++)for(let oy=-1;oy<2;oy++){
      const b=grid.get((gx+ox)+':'+(gy+oy));if(!b)continue;
      for(const j of b){if(j<=i)continue;
        let dx=X[i]-X[j],dy=Y[i]-Y[j],d2=dx*dx+dy*dy;
        if(d2<1e-4){dx=(i-j)*.01;dy=.01;d2=.0002}
        if(d2>9000)continue;const f=kr/d2;
        VX[i]+=dx*f;VY[i]+=dy*f;VX[j]-=dx*f;VY[j]-=dy*f}}}
  const ks=.03*alpha;
  for(const[a,b]of D.e){const dx=X[b]-X[a],dy=Y[b]-Y[a],
    d=Math.sqrt(dx*dx+dy*dy)||1,f=ks*(d-46)/d;
    VX[a]+=dx*f;VY[a]+=dy*f;VX[b]-=dx*f;VY[b]-=dy*f}
  const kg=.012*alpha;
  for(let i=0;i<n;i++){if(i===dragN){VX[i]=VY[i]=0;continue}
    VX[i]-=X[i]*kg;VY[i]-=Y[i]*kg;
    X[i]+=VX[i]*=.82;Y[i]+=VY[i]*=.82}
  alpha*=.986;dirty=true}
function screen(i){return[X[i]*sc+tx,Y[i]*sc+ty]}
function visible(i){return folderOn[D.n[i][2]]}
function draw(){cx.setTransform(dpr,0,0,dpr,0,0);cx.clearRect(0,0,W,H);
  const focus=sel>=0?sel:hover,hasFocus=focus>=0;
  cx.lineWidth=1;
  cx.strokeStyle='rgba(215,218,224,.07)';cx.beginPath();
  for(const[a,b]of D.e){if(!visible(a)||!visible(b))continue;
    const[x1,y1]=screen(a),[x2,y2]=screen(b);
    if((x1<0&&x2<0)||(x1>W&&x2>W)||(y1<0&&y2<0)||(y1>H&&y2>H))continue;
    cx.moveTo(x1,y1);cx.lineTo(x2,y2)}
  cx.stroke();
  if(hasFocus){cx.strokeStyle=D.c[D.n[focus][2]];cx.globalAlpha=.55;cx.beginPath();
    for(const[a,b]of D.e){if(a!==focus&&b!==focus)continue;
      if(!visible(a)||!visible(b))continue;
      const[x1,y1]=screen(a),[x2,y2]=screen(b);cx.moveTo(x1,y1);cx.lineTo(x2,y2)}
    cx.stroke();cx.globalAlpha=1}
  for(let i=0;i<n;i++){if(!visible(i))continue;
    const[x,y]=screen(i);if(x<-20||x>W+20||y<-20||y>H+20)continue;
    const r=R[i]*Math.min(sc,1.6),fade=hasFocus&&i!==focus&&!nbrs.has(i);
    cx.globalAlpha=fade?.10:1;
    cx.fillStyle=D.c[D.n[i][2]];
    cx.beginPath();cx.arc(x,y,Math.max(r,1.4),0,7);cx.fill();
    if(i===focus){cx.strokeStyle='#fff';cx.lineWidth=1.5;cx.stroke();cx.lineWidth=1}}
  cx.globalAlpha=1;cx.fillStyle='#c9cdd4';cx.font='11px system-ui,sans-serif';
  for(let i=0;i<n;i++){if(!visible(i))continue;
    const show=i===focus||nbrs.has(i)&&sel>=0||(!hasFocus&&R[i]*sc>=7.5)||sc>2.6;
    if(!show)continue;const[x,y]=screen(i);
    if(x<-20||x>W+20||y<-20||y>H+20)continue;
    cx.globalAlpha=(hasFocus&&i!==focus&&!nbrs.has(i))?.12:.92;
    cx.fillText(D.n[i][0].slice(0,42),x+R[i]*Math.min(sc,1.6)+4,y+3)}
  cx.globalAlpha=1}
function loop(){if(alpha>.004)tick();if(dirty){draw();dirty=false}requestAnimationFrame(loop)}
function pick(mx,my){let best=-1,bd=1e9;
  for(let i=0;i<n;i++){if(!visible(i))continue;const[x,y]=screen(i),
    dx=mx-x,dy=my-y,d=dx*dx+dy*dy,rr=Math.max(R[i]*Math.min(sc,1.6),4)+4;
    if(d<rr*rr&&d<bd){bd=d;best=i}}return best}
function setFocus(){const f=sel>=0?sel:hover;nbrs=new Set(f>=0?adj[f]:[]);dirty=true}
cv.addEventListener('mousedown',e=>{const i=pick(e.clientX,e.clientY);
  if(i>=0){dragN=i;alpha=Math.max(alpha,.12)}else{panning=true;cv.style.cursor='grabbing'}
  px=e.clientX;py=e.clientY;moveDist=0});
addEventListener('mousemove',e=>{
  if(dragN>=0||panning)moveDist+=Math.abs(e.clientX-px)+Math.abs(e.clientY-py);
  if(dragN>=0){X[dragN]+=(e.clientX-px)/sc;Y[dragN]+=(e.clientY-py)/sc;
    alpha=Math.max(alpha,.08);px=e.clientX;py=e.clientY;dirty=true;return}
  if(panning){tx+=e.clientX-px;ty+=e.clientY-py;px=e.clientX;py=e.clientY;dirty=true;return}
  const i=pick(e.clientX,e.clientY);
  if(i!==hover){hover=i;setFocus()}
  if(i>=0){const d=D.n[i];tip.style.display='block';
    tip.style.left=Math.min(e.clientX+14,W-330)+'px';tip.style.top=(e.clientY+14)+'px';
    tip.innerHTML='<b></b><div class="m"></div>';
    tip.firstChild.textContent=d[0];
    tip.lastChild.textContent=d[1]+' · '+D.f[d[2]]+' · '+d[3]+' backlinks · '+d[4]+' links out';
    cv.style.cursor='pointer'}
  else{tip.style.display='none';if(!panning)cv.style.cursor='grab'}});
addEventListener('mouseup',()=>{dragN=-1;panning=false;cv.style.cursor='grab'});
cv.addEventListener('click',e=>{if(moveDist>4)return;
  const i=pick(e.clientX,e.clientY);
  sel=(i===sel)?-1:i;setFocus()});
cv.addEventListener('wheel',e=>{e.preventDefault();
  const f=Math.exp(-e.deltaY*.0012),ns=Math.min(8,Math.max(.12,sc*f));
  tx=e.clientX-(e.clientX-tx)*ns/sc;ty=e.clientY-(e.clientY-ty)*ns/sc;
  sc=ns;dirty=true},{passive:false});
const legend=document.getElementById('legend');
D.f.forEach((f,i)=>{const c=document.createElement('div');c.className='chip';
  c.innerHTML='<span class="dot"></span><span></span>';
  c.firstChild.style.background=D.c[i];c.lastChild.textContent=f;
  c.title='click to show/hide';c.onclick=()=>{folderOn[i]=!folderOn[i];
    c.classList.toggle('off',!folderOn[i]);dirty=true};legend.appendChild(c)});
const box=document.getElementById('search');
box.addEventListener('keydown',e=>{if(e.key!=='Enter')return;
  const q=box.value.trim().toLowerCase();if(!q)return;
  let i=D.n.findIndex((d,j)=>visible(j)&&d[0].toLowerCase().includes(q));
  if(i<0)i=D.n.findIndex((d,j)=>visible(j)&&d[1].toLowerCase().includes(q));
  if(i<0){box.style.borderColor='#C0392B';return}
  box.style.borderColor='#3a3d44';sel=i;setFocus();
  sc=Math.max(sc,1.6);tx=W/2-X[i]*sc;ty=H/2-Y[i]*sc;dirty=true});
stats.textContent=D.count+' notes · '+D.e.length+' links · map built '+
  new Date(D.built*1000).toISOString().slice(0,10);
loop();
</script></body></html>
"""


# ---------- section search (trial) ----------
# Ranks SECTIONS (the text under one heading), not whole files, so a long log cannot win by size.
# Scoring: whole words only; BM25 (rare words weigh more, length does not help); small bonuses when a word
# sits in the section's heading, the note's title or its tags; coverage (matching more of the question
# ranks higher). Selection after Graphify's seeds: drop results far below the top, and keep at least one
# result for every question word that matched anything. Read-only: the section index lives in memory.
import math
from collections import Counter

SECTION_CHARS = 3000
_WORD = re.compile(r"[a-z0-9]+")


def _words(text):
    return _WORD.findall(text.lower())


def _split_long(body):
    """Cut a long section at paragraph breaks (then at spaces) into pieces of at most SECTION_CHARS."""
    if len(body) <= SECTION_CHARS:
        return [body]
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", body):
        while len(para) > SECTION_CHARS:
            cut = para.rfind(" ", 0, SECTION_CHARS)
            cut = cut if cut > SECTION_CHARS // 2 else SECTION_CHARS
            if cur:
                out.append(cur); cur = ""
            out.append(para[:cut]); para = para[cut:].lstrip()
        if cur and len(cur) + len(para) + 2 > SECTION_CHARS:
            out.append(cur); cur = ""
        cur = (cur + "\n\n" + para) if cur else para
    if cur.strip():
        out.append(cur)
    return out


def _sections(text):
    """(heading, text) pairs: the text under each heading, long ones cut into pieces."""
    if text.startswith("---"):
        end = text.find("\n---", 3, 8000)
        if end > 0:
            text = text[end + 4:]
    out, head, cur = [], "", []

    def flush():
        body = "\n".join(cur).strip()
        if body:
            for piece in _split_long(body):
                out.append((head, piece))

    for line in text.split("\n"):
        m = HEADING.match(line)
        if m:
            flush(); head, cur = m.group(2).strip(), []
        else:
            cur.append(line)
    flush()
    return out


def _cache_path(vault):
    import hashlib
    d = os.path.join(os.path.expanduser("~"), ".cache", "vault-map")
    os.makedirs(d, mode=0o700, exist_ok=True)
    return os.path.join(d, "sections-" + hashlib.sha1(os.path.abspath(vault).encode()).hexdigest()[:16] + ".pickle")


def _file_units(text):
    """[(heading, start, end, tf)] for one note; start/end locate the section text in the note."""
    out, cursor = [], 0
    for head, piece in _sections(text):
        tf = Counter(_words(piece))
        if not tf:
            continue
        at = text.find(piece[:200], cursor)
        if at < 0:
            at = text.find(piece[:200])
        end = at + len(piece) if at >= 0 else -1
        out.append((head, at, end, tf))
        if at >= 0:
            cursor = at + 1
    return out


def section_index(vault):
    """Section index, kept in ~/.cache/vault-map (never inside the vault). Only changed notes are re-read."""
    import pickle
    cp = _cache_path(vault)
    cache = {}
    try:
        with open(cp, "rb") as fh:
            cache = pickle.load(fh)
    except (OSError, EOFError, pickle.UnpicklingError, AttributeError, ValueError):
        cache = {}
    mp = {}
    path = os.path.join(vault, ".vault-map.json")
    if os.path.exists(path):
        mp = json.load(open(path)).get("notes", {})
    by_rel = {n["rel"]: n for n in mp.values()}
    files, changed = {}, False
    for root, dirs, fs in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in fs:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault)
            try:
                st = os.stat(full)
            except OSError:
                continue
            key = (int(st.st_mtime), st.st_size)
            hit = cache.get(rel)
            if hit and hit[0] == key:
                files[rel] = hit
                continue
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            files[rel] = (key, _file_units(text))
            changed = True
    if changed or len(files) != len(cache):
        tmp = cp + ".tmp"
        with open(tmp, "wb") as fh:
            pickle.dump(files, fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.chmod(tmp, 0o600)
        os.replace(tmp, cp)
    units, df = [], Counter()
    for rel, (_, us) in files.items():
        n = by_rel.get(rel, {})
        title = n.get("title") or os.path.basename(rel)[:-3]
        tw, gw = set(_words(title)), set(t for tag in n.get("tags", []) for t in _words(tag))
        for head, start, end, tf in us:
            units.append({"rel": rel, "title": title, "heading": head, "start": start, "end": end, "tf": tf,
                          "len": sum(tf.values()), "hw": set(_words(head)), "tw": tw, "gw": gw, "note": n})
            df.update(tf.keys())
    avg = (sum(u["len"] for u in units) / len(units)) if units else 1.0
    return {"units": units, "df": df, "n": len(units), "avg": avg, "vault": vault}


def _unit_text(vault, u):
    try:
        text = open(os.path.join(vault, u["rel"]), encoding="utf-8", errors="replace").read()
    except OSError:
        return ""
    if u["start"] >= 0 and u["end"] > u["start"]:
        return text[u["start"]:u["end"]]
    for head, piece in _sections(text):
        if head == u["heading"] and Counter(_words(piece)) == u["tf"]:
            return piece
    return ""


_SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def _span_score(text, weights):
    return sum(weights.get(w, 0.0) for w in set(_WORD.findall(text.lower())))


def best_window(text, terms, width=150, weights=None):
    """The best <= width chars of `text` for the question: whole sentences around the question's (rare) words.
    The best sentence first; a neighbouring sentence is added while it fits; a sentence longer than the
    window is cut around the densest cluster of question words, not from the first word."""
    weights = weights or {t: 1.0 for t in terms}
    sents = [x.strip() for x in _SENT.split(text) if x and x.strip()]
    if not sents:
        return text[:width]
    scores = [_span_score(x, weights) for x in sents]
    i = max(range(len(sents)), key=lambda k: (scores[k], -len(sents[k])))
    best = sents[i]
    if len(best) > width:
        toks = [(m.start(), m.group()) for m in _WORD.finditer(best.lower())]
        hits = [p for p, w in toks if w in weights]
        if hits:
            centre = (min(hits) + max(hits)) // 2 if max(hits) - min(hits) < width else hits[0] + width // 4
            start = max(0, min(len(best) - width, centre - width // 2))
            sp = best.rfind(" ", 0, start + 1)
            start = sp + 1 if 0 <= sp and start - sp < 20 else start
            return best[start:start + width].strip()
        return best[:width]
    lo, hi = i, i
    while True:
        cands = []
        if lo > 0 and len(" ".join(sents[lo - 1:hi + 1])) <= width:
            cands.append((scores[lo - 1], lo - 1, hi))
        if hi + 1 < len(sents) and len(" ".join(sents[lo:hi + 2])) <= width:
            cands.append((scores[hi + 1], lo, hi + 1))
        if not cands:
            break
        _, lo, hi = max(cands)
    return " ".join(sents[lo:hi + 1])


def query_sections(terms, vault, top_n=8, as_json=False):
    """Command-line printer over search_sections(): path, heading and passage per result."""
    if not os.path.exists(os.path.join(vault, ".vault-map.json")):
        print(json.dumps({"error": "no map — run build first"}) if as_json else "no map — run build first")
        return
    res = search_sections(terms, vault, top_n)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return
    if not res["results"]:
        print(f"no notes match: {res['query']}"); return
    print(f"vault-map query '{res['query']}' — {res['hits']} hits, top {len(res['results'])} sections:")
    for r in res["results"]:
        print(f"\n[{r['score']}] {r['path']}")
        print(f"    section: {r.get('section') or '-'}")
        print(f"    {r.get('text', '')}")
        if r.get("also_in"):
            print(f"    also in: {', '.join(r['also_in'])}")


def search_sections(terms, vault, top_n=8, index=None, k1=1.2, b=0.75, floor=0.2):
    """Rank sections against `terms`; returns the same shape as search() plus `section` and `text`."""
    ix = index or section_index(vault)
    terms = list(dict.fromkeys(w for t in terms for w in _words(t)))
    if not terms or not ix["units"]:
        return {"query": " ".join(terms), "hits": 0, "results": []}
    if top_n <= 0:  # asking for no results: nothing to rank (and nothing for the coverage loop to pop)
        return {"query": " ".join(terms), "hits": 0, "results": []}
    N, df, avg = ix["n"], ix["df"], ix["avg"]
    idf = {t: math.log(1 + (N - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5)) for t in terms}
    scored, best_for = [], {}
    for i, u in enumerate(ix["units"]):
        s, matched = 0.0, 0
        for t in terms:
            tf = u["tf"].get(t, 0)
            here = tf or t in u["hw"] or t in u["tw"] or t in u["gw"]
            if not here:
                continue
            matched += 1
            if tf:
                s += idf[t] * tf * (k1 + 1) / (tf + k1 * (1 - b + b * u["len"] / avg))
            if t in u["hw"]: s += idf[t] * 1.0
            if t in u["tw"]: s += idf[t] * 0.5
            if t in u["gw"]: s += idf[t] * 0.5
        if not matched:
            continue
        s *= 0.25 + 0.75 * matched / len(terms)
        scored.append((s, i))
        for t in terms:
            if t in u["tf"] and (t not in best_for or s > best_for[t][0]):
                best_for[t] = (s, i)
    scored.sort(reverse=True)
    top = scored[0][0] if scored else 0
    # Pick results in score order. The same words reaching us from several notes (a session exported twice, its
    # codex log) are shown ONCE: the stronger copy stays and lists the others in `also_in`.
    vlt = ix.get("vault", vault)
    results, by_window, seen_pos = [], {}, set()

    def make(s, i):
        u = ix["units"][i]; n = u["note"]; full = _unit_text(vlt, u)
        win = best_window(full, terms, weights=idf).replace("\n", " ")
        return {"path": u["rel"], "title": u["title"], "score": round(s, 3), "bytes": n.get("bytes"),
                "modified": time.strftime("%Y-%m-%d", time.localtime(n["mtime"])) if n.get("mtime") else None,
                "sections": (n.get("headings") or [])[1:4], "snippet": win,
                "links": (n.get("links") or [])[:5], "backlinks": (n.get("backlinks") or [])[:5],
                "section": u["heading"], "text": full, "also_in": [], "_i": i}

    def add(s, i):
        u = ix["units"][i]
        pos = (u["rel"], u["start"]) if u["start"] >= 0 else (u["rel"], u["heading"], i)
        if pos in seen_pos:
            return False
        seen_pos.add(pos)
        r = make(s, i)
        key = " ".join(_words(r["snippet"]))
        if key and key in by_window:
            first = by_window[key]
            if r["path"] != first["path"] and r["path"] not in first["also_in"]:
                first["also_in"].append(r["path"])
            return False
        by_window[key] = r
        results.append(r)
        return True

    for s, i in scored:
        if s < top * floor or len(results) >= top_n:
            break
        add(s, i)
    # one result per matched question word, if the cut left a word with none
    for t, (s, i) in sorted(best_for.items(), key=lambda kv: -kv[1][0]):
        if any(t in ix["units"][r["_i"]]["tf"] for r in results):
            continue
        if len(results) >= top_n:
            gone = results.pop()
            by_window = {k: v for k, v in by_window.items() if v is not gone}
        add(s, i)
    for r in results:
        r.pop("_i", None)
    return {"query": " ".join(terms), "hits": len(scored), "results": results}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in ("build", "query", "graph", "path"):
        print(__doc__); sys.exit(1)
    cmd = args.pop(0)
    top_n = 8
    if "--n" in args:
        i = args.index("--n")
        if i + 1 >= len(args):
            print("--n needs a number"); sys.exit(1)
        top_n = int(args[i + 1]); del args[i:i + 2]
    as_json = "--json" in args
    if as_json:
        args.remove("--json")
    sections = "--sections" in args
    if sections:
        args.remove("--sections")
    out = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 >= len(args):
            print("--out needs a file path"); sys.exit(1)
        out = args[i + 1]; del args[i:i + 2]
    if cmd == "build":
        build(args[0] if args else DEFAULT_VAULT)
    elif cmd == "graph":
        graph_cmd(args[0] if args else DEFAULT_VAULT, out)
    elif cmd == "path":
        if len(args) < 2:
            print(__doc__); sys.exit(1)
        path_cmd(args[0], args[1], args[2] if len(args) > 2 else DEFAULT_VAULT)
    else:
        qterms = args[0].split() if args else []
        vault = args[1] if len(args) > 1 else DEFAULT_VAULT
        query(qterms, vault, top_n, as_json, sections)
