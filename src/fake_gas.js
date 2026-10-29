// Faux Google Apps Script pour les tests : exécute nuage/signer.gs tel quel, avec un faux Google Drive (un dossier du disque).
// Usage : node nuage/fake_gas.js <dossier racine du faux Drive> <port>
const fs = require("fs"), path = require("path"), crypto = require("crypto"), vm = require("vm"), http = require("http");
const ROOT = path.resolve(process.argv[2]), PORT = Number(process.argv[3] || 8093);
const PROPS = path.join(ROOT, ".props.json"), MAILS = path.join(ROOT, ".mails.json");
const rj = (f, d) => { try { return JSON.parse(fs.readFileSync(f, "utf8")); } catch(e){ return d; } };
const signed = buf => Array.from(buf, b => b > 127 ? b - 256 : b);
const iter = arr => { let i = 0; return {hasNext: () => i < arr.length, next: () => arr[i++]}; };
const blob = (data, type, name) => ({data: typeof data === "string" ? Buffer.from(data, "utf8") : Buffer.from(Array.from(data, b => (b + 256) % 256)), type, name,
  getDataAsString(){ return this.data.toString("utf8"); }, getBytes(){ return signed(this.data); }, getName(){ return this.name; }});
function File(p){ return {getId: () => p, getName: () => path.basename(p), getLastUpdated: () => fs.statSync(p).mtime, getBlob: () => blob(fs.readFileSync(p), "", path.basename(p)), isTrashed: () => false}; }
function Folder(p){
  const kids = () => fs.readdirSync(p).filter(n => !n.startsWith("."));
  return {getId: () => p, getName: () => path.basename(p), isTrashed: () => false,
    getFilesByName: n => iter(kids().filter(k => k === n && fs.statSync(path.join(p, k)).isFile()).map(k => File(path.join(p, k)))),
    getFoldersByName: n => iter(kids().filter(k => k === n && fs.statSync(path.join(p, k)).isDirectory()).map(k => Folder(path.join(p, k)))),
    createFile: b => { fs.writeFileSync(path.join(p, b.name), b.data); return File(path.join(p, b.name)); }};
}
const allFolders = (p, out) => { for (const n of fs.readdirSync(p)){ const q = path.join(p, n); if (!n.startsWith(".") && fs.statSync(q).isDirectory()){ out.push(q); allFolders(q, out); } } return out; };
const ctx = {
  console, JSON, Math, Date, Number, String, Array, Object, encodeURIComponent,
  DriveApp: {getFoldersByName: n => iter(allFolders(ROOT, []).filter(q => path.basename(q) === n).map(Folder)), getFolderById: id => { if (!fs.existsSync(id)) throw new Error("introuvable"); return Folder(id); }},
  Utilities: {
    computeHmacSha256Signature: (v, k) => signed(crypto.createHmac("sha256", k).update(v, "utf8").digest()),
    base64Decode: s => signed(Buffer.from(s, "base64")),
    newBlob: blob,
    formatDate: (d, tz, f) => { const p = Object.fromEntries(new Intl.DateTimeFormat("en-CA", {timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23"}).formatToParts(d).map(x => [x.type, x.value]));
      return f.replace("yyyy", p.year).replace("MM", p.month).replace("dd", p.day).replace("HH", p.hour).replace("mm", p.minute); }
  },
  PropertiesService: {getScriptProperties: () => ({getProperty: k => { const v = rj(PROPS, {})[k]; return v == null ? null : v; },
    setProperty: (k, v) => { const o = rj(PROPS, {}); o[k] = String(v); fs.writeFileSync(PROPS, JSON.stringify(o)); },
    deleteProperty: k => { const o = rj(PROPS, {}); delete o[k]; fs.writeFileSync(PROPS, JSON.stringify(o)); }})},
  LockService: {getScriptLock: () => ({tryLock: () => true, releaseLock(){}})},
  MailApp: {sendEmail: o => { const L = rj(MAILS, []); L.push({to: o.to, subject: o.subject, body: o.body, name: o.name, attachments: (o.attachments || []).map(a => [a.name, a.type, a.data.length])}); fs.writeFileSync(MAILS, JSON.stringify(L, null, 1)); }, getRemainingDailyQuota: () => 100},
  Session: {getEffectiveUser: () => ({getEmail: () => "emondagehamel@gmail.com"})},
  ContentService: {MimeType: {JSON: "json"}, createTextOutput: s => ({content: s, setMimeType(){ return this; }})}
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, "signer.gs"), "utf8"), ctx, {filename: "signer.gs"});
http.createServer((req, res) => {
  const u = new URL(req.url, "http://x"), send = (code, s) => { res.writeHead(code, {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}); res.end(s); };
  if (!/^\/macros\/s\/[\w-]+\/exec$/.test(u.pathname)) return send(404, "{}");
  if (req.method === "GET") { try { return send(200, ctx.doGet({parameter: Object.fromEntries(u.searchParams)}).content); } catch(e){ console.error(e); return send(500, "{}"); } }
  if (req.method === "POST"){ let b = ""; req.on("data", c => b += c); req.on("end", () => { try { send(200, ctx.doPost({postData: {contents: b}}).content); } catch(e){ console.error(e); send(500, "{}"); } }); return; }
  send(405, "{}");
}).listen(PORT, "127.0.0.1", () => console.log("faux Apps Script prêt sur " + PORT));
