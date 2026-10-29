"""v3.4 (1/2) : changements génériques venant du téléphone (patch, fichiers)."""
import sys
P = sys.argv[1]; s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit("ATTENDU %d, TROUVÉ %d : %s" % (n, c, a[:90]))
    s = s.replace(a, b)
rep('''function applyOp(d, op){
  const x = op.data || {}, now = op.creeLe || new Date().toISOString(), res = {msg:"", moves:[], pdf:null};''',
'''/* Changements que cette version de l'application sait appliquer (écrit dans registre.json pour le téléphone) */
const OPS_CONNUS = ["evenement","evenement-suppr","evenement-fait","obligation","operation","photo","trajet","lieu","lieu-suppr","paiement","facture","devis","devis-statut","envoye","entretien","odometre","client","patch","fichier","deplacer","fichier-suppr"];
/* Chemin de fichier accepté venant du téléphone : un seul niveau, dans un dossier connu */
function safePath(p){ p = String(p || ""); return /^(recus|a-traiter|documents|exports)\\/[^\\/\\\\:*?"<>|]+$/.test(p) && !/\\.\\./.test(p) ? p : ""; }
function applyOp(d, op){
  const x = op.data || {}, now = op.creeLe || new Date().toISOString(), res = {msg:"", moves:[], removes:[], pdf:null, pdfs:[]};''')
rep('''    case "client": { if (!x.nom) break; const c = d.clients.find(e => (x.id && e.id === x.id) || norm(e.nom) === norm(x.nom)); if (c) Object.assign(c, x, {id: c.id}); else d.clients.push(Object.assign({id: x.id || uid("c"), courriel:"", telephone:"", adresse:"", note:""}, x)); res.msg = "Client : " + x.nom; break; }''',
'''    case "client": { if (!x.nom) break; const c = d.clients.find(e => (x.id && e.id === x.id) || norm(e.nom) === norm(x.nom)); if (c) Object.assign(c, x, {id: c.id}); else d.clients.push(Object.assign({id: x.id || uid("c"), courriel:"", telephone:"", adresse:"", note:""}, x)); res.msg = "Client : " + x.nom; break; }
    /* Modification faite dans la version complète du téléphone : champs changés, fiches ajoutées ou retirées */
    case "patch": {
      (Array.isArray(x.changes) ? x.changes : []).forEach(c => {
        if (!c || typeof c !== "object") return;
        if (c.col === "reglages"){ d.reglages = d.reglages || {}; Object.assign(d.reglages, clone(c.set || {})); (c.unset || []).forEach(k => { delete d.reglages[k]; }); return; }
        if (!COLLECTIONS.includes(c.col) || !c.id || !Array.isArray(d[c.col])) return;
        const L = d[c.col], i = L.findIndex(e => e && e.id === c.id);
        if (c.suppr){ if (i >= 0) L.splice(i, 1); return; }
        if (i < 0){ if (!c.doc || c.doc.id !== c.id) return; L.push(clone(c.doc)); }
        else if (c.doc) L[i] = clone(c.doc);
        else { Object.assign(L[i], clone(c.set || {})); (c.unset || []).forEach(k => { delete L[i][k]; }); }
        if (c.col === "factures" || c.col === "devis") res.pdfs.push([c.col === "factures" ? "facture" : "devis", c.id]);
      });
      res.msg = x.msg || "Modification faite au téléphone"; break; }
    case "fichier": { const to = safePath(x.to); if (to && photos[0]) res.moves.push({from:"telephone/" + photos[0], to}); break; }
    case "deplacer": { const a = safePath(x.from), b = safePath(x.to); if (a && b) res.moves.push({from:a, to:b}); break; }
    case "fichier-suppr": { const p = safePath(x.path); if (p) res.removes.push(p); break; }''')
rep('''    default: res.msg = "";
  }
  return res;''', '''    default: res.unknown = true;
  }
  return res;''')
# réception sur l'ordinateur
rep('''    const refd = new Set(ops.flatMap(o => o.op.photos || []));''', '''    if (String((S.d.telephone || {}).ops || "") !== OPS_CONNUS.join(",")) await mutate(d => { d.telephone = d.telephone && typeof d.telephone === "object" ? d.telephone : {}; d.telephone.ops = OPS_CONNUS.slice(); });
    const refd = new Set(ops.flatMap(o => o.op.photos || []));''')
rep('''    const msgs = [], pdfs = []; let count = 0;''', '''    const msgs = [], pdfs = [], unknown = new Set(); let count = 0;''')
rep('''        let r; try { r = applyOp(d, o.op); } catch(e){ console.error(e); continue; }
        for (const m of r.moves){ try { await moveFile(m.from, m.to); } catch(e){} }
        if (r.pdf) pdfs.push(r.pdf); if (r.msg) msgs.push(r.msg); seen.add(o.op.id); count++;
      }
      d.telephone.appliques = [...seen].slice(-400); d.telephone.dernier = new Date().toISOString();''',
'''        let r; try { r = applyOp(d, o.op); } catch(e){ console.error(e); continue; }
        if (r.unknown){ unknown.add(o.name); continue; }   // version plus récente du téléphone : on garde le fichier pour une mise à jour
        for (const m of r.moves){ try { await moveFile(m.from, m.to); } catch(e){} }
        for (const p of r.removes || []){ try { await removeFile(p); } catch(e){} }
        if (r.pdf) pdfs.push(r.pdf); (r.pdfs || []).forEach(p => pdfs.push(p)); if (r.msg) msgs.push(r.msg); seen.add(o.op.id); count++;
      }
      d.telephone.appliques = [...seen].slice(-400); d.telephone.dernier = new Date().toISOString(); d.telephone.ops = OPS_CONNUS.slice();''')
rep('''    for (const o of ready){ try { await dir.removeEntry(o.name); } catch(e){} }
    for (const [k, id] of pdfs){ try { await makeDocPDF(k, id, false, true); } catch(e){} }''',
'''    for (const o of ready){ if (unknown.has(o.name)) continue; try { await dir.removeEntry(o.name); } catch(e){} }
    const pk = new Set(); for (const [k, id] of pdfs){ if (pk.has(k + id)) continue; pk.add(k + id); try { await makeDocPDF(k, id, false, true); } catch(e){} }
    if (unknown.size) toast(unknown.size + " changement(s) du téléphone attendent une mise à jour de cette application");''')
open(P, "w", encoding="utf-8").write(s); print("ok")
