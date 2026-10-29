// Vérifie SHA256/hmacHex de signer_core.js contre le module crypto de Node
const fs = require("fs"), crypto = require("crypto"), vm = require("vm");
const ctx = {TextEncoder, URLSearchParams, encodeURIComponent, Math, Array, Uint8Array, Uint32Array, DataView, window: {}, R: () => ({}), docTotals: () => ({total: 0})};
vm.createContext(ctx); vm.runInContext(fs.readFileSync("nuage/signer_core.js", "utf8") + "\nthis.SHA256 = SHA256; this.hmacHex = hmacHex;", ctx);
let bad = 0, n = 0;
for (let len = 0; len < 300; len++){
  const m = crypto.randomBytes(len);
  const a = Buffer.from(ctx.SHA256(new Uint8Array(m))).toString("hex"), b = crypto.createHash("sha256").update(m).digest("hex");
  if (a !== b){ bad++; if (bad < 3) console.log("sha", len, a, b); } n++;
}
for (const [k, msg] of [["abc", ""], ["0123456789abcdef0123456789abcdef", "v1|dv-1|D-2026-010|Michel%20Auger|45990|2026-11-28|%C3%89mondage%20Hamel"], ["x".repeat(100), "é".repeat(500)]]){
  const a = ctx.hmacHex(k, msg), b = crypto.createHmac("sha256", k).update(msg, "utf8").digest("hex"); if (a !== b){ bad++; console.log("hmac", k.length, a, b); } n++;
}
console.log("SHA/HMAC :", n, "essais,", bad, "erreurs");
