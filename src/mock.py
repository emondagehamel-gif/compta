"""Serveurs de test : l'application (port 8090, /compta/) et un faux Google (port 8091 : connexion + Drive v3)."""
import json, base64, re, threading, os, time, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
FOLDER = "application/vnd.google-apps.folder"
STATE = {"files": {}, "n": 0, "auth": "ok", "tok": 0, "valid": set(), "log": [], "calls": 0, "osrm": "ok", "routes": 0}

def reset(reg_text):
    F = STATE["files"] = {}
    def add(**o):
        o.setdefault("modifiedTime", time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())); o.setdefault("mimeType", "application/octet-stream"); o.setdefault("trashed", False)
        F[o["id"]] = o
    add(id="root1", name="Comptabilite", mimeType=FOLDER, parents=["myroot"])
    add(id="old1", name="Comptabilite", mimeType=FOLDER, parents=["myroot"])
    add(id="tel1", name="telephone", mimeType=FOLDER, parents=["root1"])
    add(id="docs1", name="documents", mimeType=FOLDER, parents=["root1"])
    add(id="reg1", name="registre.json", mimeType="application/json", parents=["root1"], content=reg_text.encode())
    STATE["auth"] = "ok"; STATE["valid"] = set(); STATE["log"] = []; STATE["n"] = 0

def match(f, q):
    for c in [c.strip() for c in q.split(" and ")]:
        m = re.match(r"^(\w+) = '((?:[^'\\]|\\.)*)'$", c)
        m2 = re.match(r"^'((?:[^'\\]|\\.)*)' in parents$", c)
        if m:
            v = m.group(2).replace("\\'", "'").replace("\\\\", "\\")
            if str(f.get(m.group(1))) != v: return False
        elif m2:
            if m2.group(1) not in f.get("parents", []): return False
        elif c == "trashed = false":
            if f.get("trashed"): return False
        else:
            raise ValueError("requête non comprise : " + c)
    return True

class G(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type"); self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    def out(self, code, obj=None, raw=None, ctype="application/json"):
        body = raw if raw is not None else json.dumps(obj if obj is not None else {}).encode()
        self.send_response(code); self.cors(); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self): self.send_response(204); self.cors(); self.end_headers()
    def authed(self):
        h = self.headers.get("Authorization", "")
        if not h.startswith("Bearer ") or h[7:] not in STATE["valid"]:
            self.out(401, {"error": {"code": 401, "message": "Invalid Credentials"}}); return False
        STATE["calls"] += 1; return True
    def do_GET(self):
        u = urllib.parse.urlsplit(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/o/oauth2/v2/auth":
            STATE["log"].append({"prompt": q.get("prompt"), "hint": q.get("login_hint", ""), "scope": q.get("scope"), "client": q.get("client_id"), "redirect": q.get("redirect_uri")})
            mode = STATE["auth"]
            if mode == "deny" and q.get("prompt") == "none": frag = {"error": "interaction_required", "state": q.get("state", "")}
            else:
                STATE["tok"] += 1; t = "tok%d" % STATE["tok"]; STATE["valid"].add(t)
                frag = {"access_token": t, "expires_in": "3599", "token_type": "Bearer", "scope": q.get("scope", ""), "state": q.get("state", "")}
            self.send_response(302); self.send_header("Location", q["redirect_uri"] + "#" + urllib.parse.urlencode(frag)); self.end_headers(); return
        m0 = re.match(r"^/route/v1/driving/([-\d.]+),([-\d.]+);([-\d.]+),([-\d.]+)$", u.path)
        if m0:
            if STATE["osrm"] != "ok": return self.out(503, {"code": "Error"})
            import math
            lo1, la1, lo2, la2 = map(float, m0.groups()); r = math.radians
            h = math.sin(r(la2 - la1) / 2) ** 2 + math.cos(r(la1)) * math.cos(r(la2)) * math.sin(r(lo2 - lo1) / 2) ** 2
            STATE["routes"] += 1
            return self.out(200, {"code": "Ok", "routes": [{"distance": round(2 * 6371000 * math.asin(math.sqrt(h)) * 1.3, 1), "duration": 900}]})
        if u.path == "/__state":
            return self.out(200, {"files": [{k: (base64.b64encode(v).decode() if k == "content" else v) for k, v in f.items()} for f in STATE["files"].values()], "log": STATE["log"], "calls": STATE["calls"], "routes": STATE["routes"]})
        if u.path == "/drive/v3/about":
            if not self.authed(): return
            return self.out(200, {"user": {"emailAddress": "emondagehamel@gmail.com", "displayName": "Emondage Hamel"}})
        if u.path == "/drive/v3/files":
            if not self.authed(): return
            try: L = [f for f in STATE["files"].values() if match(f, q.get("q", ""))]
            except ValueError as e: return self.out(400, {"error": {"code": 400, "message": str(e)}})
            L.sort(key=lambda f: f["modifiedTime"], reverse=True)
            L = L[: int(q.get("pageSize", 100))]
            return self.out(200, {"files": [{k: f[k] for k in ("id", "name", "mimeType", "modifiedTime", "parents")} for f in L]})
        m = re.match(r"^/drive/v3/files/([\w-]+)$", u.path)
        if m:
            if not self.authed(): return
            f = STATE["files"].get(m.group(1))
            if not f or f.get("trashed"): return self.out(404, {"error": {"code": 404, "message": "File not found"}})
            return self.out(200, raw=f.get("content", b""), ctype=f["mimeType"])
        self.out(404, {"error": {"message": "inconnu"}})
    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if u.path == "/__mode":
            o = json.loads(body); STATE.update({k: v for k, v in o.items() if k in ("auth", "osrm")})
            if o.get("expire"): STATE["valid"] = set()
            return self.out(200, {"ok": True})
        if u.path == "/__setreg":
            f = STATE["files"]["reg1"]; f["content"] = body; f["modifiedTime"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()); return self.out(200, {"ok": True})
        if u.path == "/__consume":
            # l'ordinateur applique les changements : il efface les fichiers op et range les photos
            for f in STATE["files"].values():
                if "tel1" in f.get("parents", []): f["trashed"] = True
            return self.out(200, {"ok": True})
        if u.path == "/upload/drive/v3/files":
            if not self.authed(): return
            ct = self.headers.get("Content-Type", ""); m = re.search(r"boundary=([^;]+)", ct)
            if not m: return self.out(400, {"error": {"message": "pas de boundary"}})
            b = ("--" + m.group(1)).encode(); parts = [p for p in body.split(b) if p.strip() and p.strip() != b"--"]
            def split(p):
                p = p[2:] if p.startswith(b"\r\n") else p
                h, _, c = p.partition(b"\r\n\r\n")
                return h, (c[:-2] if c.endswith(b"\r\n") else c)
            _, meta = split(parts[0]); _, content = split(parts[1]); meta = json.loads(meta)
            STATE["n"] += 1; fid = "new%d" % STATE["n"]
            STATE["files"][fid] = {"id": fid, "name": meta["name"], "mimeType": meta.get("mimeType", "application/octet-stream"), "parents": meta.get("parents", []), "content": content,
                                   "modifiedTime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()), "trashed": False}
            return self.out(200, {"id": fid, "name": meta["name"]})
        self.out(404, {})

class App(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/compta": self.send_response(301); self.send_header("Location", "/compta/"); self.end_headers(); return
        if not p.startswith("/compta/"): self.send_response(404); self.end_headers(); return
        rel = p[len("/compta/"):] or "index.html"; fp = os.path.join(DIST, rel)
        if not os.path.isfile(fp): self.send_response(404); self.end_headers(); return
        data = open(fp, "rb").read(); ext = os.path.splitext(fp)[1]
        ct = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".png": "image/png", ".webmanifest": "application/manifest+json"}.get(ext, "application/octet-stream")
        self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-cache"); self.end_headers(); self.wfile.write(data)

def start():
    for port, h in ((8090, App), (8091, G)):
        s = ThreadingHTTPServer(("127.0.0.1", port), h); threading.Thread(target=s.serve_forever, daemon=True).start()
