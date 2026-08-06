"""Static HTML / JSON export for the visual probe (no server, no remote assets)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import DISCLAIMER
from .model import Manifest, SceneRecord

_VIEWER_JS = r"""
(function () {
  const data = window.PROBE_SCENE;
  const canvas = document.getElementById("view");
  const ctx = canvas.getContext("2d");
  let yaw = 0.75, pitch = 0.45, dist = 1.8;
  let dragging = false, lastX = 0, lastY = 0;
  const orthographic = !!(data.camera && data.camera.orthographic);

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = Math.max(320, Math.floor(rect.width));
    canvas.height = Math.max(280, Math.floor(rect.height));
    draw();
  }

  function rotateY(p, a) {
    const c = Math.cos(a), s = Math.sin(a);
    return [c*p[0]+s*p[2], p[1], -s*p[0]+c*p[2]];
  }
  function rotateX(p, a) {
    const c = Math.cos(a), s = Math.sin(a);
    return [p[0], c*p[1]-s*p[2], s*p[1]+c*p[2]];
  }
  function project(p) {
    let q = rotateY(p, yaw);
    q = rotateX(q, pitch);
    const z = q[2] + dist;
    const f = orthographic ? 220 : 420 / Math.max(0.35, z);
    return [canvas.width/2 + q[0]*f, canvas.height/2 - q[1]*f, z];
  }

  function drawLine(a, b, color, width, dash) {
    const pa = project(a), pb = project(b);
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = width || 2;
    if (dash) ctx.setLineDash(dash); else ctx.setLineDash([]);
    ctx.moveTo(pa[0], pa[1]);
    ctx.lineTo(pb[0], pb[1]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function drawAxis(axis, length, color, label, dash) {
    const p = axis.point, d = axis.direction;
    const a = [p[0]-d[0]*length, p[1]-d[1]*length, p[2]-d[2]*length];
    const b = [p[0]+d[0]*length, p[1]+d[1]*length, p[2]+d[2]*length];
    drawLine(a, b, color, 2.5, dash);
    if (label) {
      const pe = project(b);
      ctx.fillStyle = color;
      ctx.font = "12px ui-monospace, monospace";
      ctx.fillText(label, pe[0]+4, pe[1]-4);
    }
  }

  function drawPoint(p, color, label) {
    const q = project(p);
    ctx.beginPath();
    ctx.fillStyle = color;
    ctx.arc(q[0], q[1], 4, 0, Math.PI*2);
    ctx.fill();
    if (label) {
      ctx.fillStyle = "#222";
      ctx.font = "12px ui-monospace, monospace";
      ctx.fillText(label, q[0]+6, q[1]-6);
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#f7f5f1";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const fk = data.fk || {};
    const L = fk.axis_length || 0.3;
    const opacity = data.arm_opacity == null ? 1 : data.arm_opacity;
    const linkColor = `rgba(40,40,40,${opacity})`;

    (fk.links || []).forEach(link => drawLine(link.start, link.end, linkColor, 3));
    (fk.joints || []).forEach(j => {
      const showCenters = data.show_joint_centers !== false;
      if (showCenters) drawPoint(j.origin, `rgba(20,20,20,${opacity})`, j.label);
      const selected = (data.selected_joint_indices || []).includes(j.index);
      const dim = data.dim_unselected_axes && !selected && data.selected_joint_indices;
      const col = selected ? "#0b6e4f" : (dim ? "rgba(120,120,120,0.35)" : `rgba(30,90,160,${opacity})`);
      const dash = (data.roll && data.roll.style && j.index === 6) ? [6,4] : null;
      if (data.show_unselected_axes !== false || selected || !data.selected_joint_indices) {
        drawAxis(j.axis, L, col, selected ? j.label : "", dash);
      }
    });

    if (fk.tool_point) {
      drawPoint(fk.tool_point, "#b00020", "p");
      const d = fk.pointing;
      const tip = [fk.tool_point[0]+d[0]*L*0.8, fk.tool_point[1]+d[1]*L*0.8, fk.tool_point[2]+d[2]*L*0.8];
      drawLine(fk.tool_point, tip, "#b00020", 2);
    }

    if (data.closure) {
      const c = data.closure;
      drawPoint(c.center, "#6a1b9a", "S_v");
      drawAxis(c.axes.Sx, L*0.7, "#8e24aa", "Sx");
      drawAxis(c.axes.Sy, L*0.7, "#8e24aa", "Sy");
      drawAxis(c.axes.Sz, L*0.7, "#8e24aa", "Sz");
    }

    if (data.roll) {
      drawAxis(data.roll.axis, L, "rgba(180,80,0,0.85)", data.roll.label, [7,5]);
    }

    if (data.candidate && data.candidate.axes) {
      const colors = {S:"#6a1b9a", U:"#0b6e4f", R:"#1565c0"};
      data.candidate.axes.forEach(ax => {
        drawAxis(ax.axis, L, colors[ax.role] || "#333", ax.source_id);
      });
    }

    if (data.fk_roll_compare && data.fk_roll_compare.tool_transform === undefined) {
      // ghost tool frame axes from roll compare via pointing only
      const g = data.fk_roll_compare;
      if (g.tool_point && g.pointing) {
        const tip = [g.tool_point[0]+g.pointing[0]*L*0.5, g.tool_point[1]+g.pointing[1]*L*0.5, g.tool_point[2]+g.pointing[2]*L*0.5];
        drawLine(g.tool_point, tip, "rgba(180,80,0,0.5)", 2, [4,3]);
      }
    }
  }

  canvas.addEventListener("mousedown", e => { dragging = true; lastX = e.clientX; lastY = e.clientY; });
  window.addEventListener("mouseup", () => dragging = false);
  window.addEventListener("mousemove", e => {
    if (!dragging) return;
    yaw += (e.clientX - lastX) * 0.01;
    pitch += (e.clientY - lastY) * 0.01;
    pitch = Math.max(-1.2, Math.min(1.2, pitch));
    lastX = e.clientX; lastY = e.clientY;
    draw();
  });
  canvas.addEventListener("wheel", e => {
    dist *= (e.deltaY > 0 ? 1.08 : 0.92);
    dist = Math.max(0.6, Math.min(4.5, dist));
    draw();
    e.preventDefault();
  }, {passive:false});

  window.addEventListener("resize", resize);
  resize();
})();
"""

_SCENE_CSS = """
:root { color-scheme: light; }
body { margin:0; font-family: "IBM Plex Sans", "Source Sans 3", "Segoe UI", sans-serif;
  background:#efece6; color:#1c1b19; }
header { padding:1rem 1.25rem; border-bottom:1px solid #cfc8bb; background:#f7f5f1; }
header h1 { margin:0 0 .35rem; font-size:1.25rem; }
.disclaimer { font-size:.85rem; color:#6b3a00; background:#fff3cd; padding:.5rem .75rem; border-radius:4px; }
main { display:grid; grid-template-columns: 1.4fr .9fr; gap:1rem; padding:1rem; min-height:70vh; }
#view-wrap { background:#f7f5f1; border:1px solid #cfc8bb; min-height:480px; }
#view { width:100%; height:100%; display:block; }
aside { background:#f7f5f1; border:1px solid #cfc8bb; padding:1rem; }
aside h2 { margin-top:0; font-size:1rem; }
ul { padding-left:1.1rem; }
code, .mono { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size:.85rem; }
@media (max-width: 900px) { main { grid-template-columns: 1fr; } }
"""


def _html_page(title: str, scene: dict[str, Any], *, extra_controls: str = "") -> str:
    payload = json.dumps(scene, indent=2)
    notes = scene.get("notes") or []
    notes_html = "\n".join(f"<li>{n}</li>" for n in notes)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>{_SCENE_CSS}</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <div class="disclaimer">{scene.get("disclaimer", DISCLAIMER)}</div>
</header>
<main>
  <div id="view-wrap"><canvas id="view"></canvas></div>
  <aside>
    <h2>Notes</h2>
    <ul>{notes_html}</ul>
    {extra_controls}
    <h2>Legend</h2>
    <ul>
      <li>Blue/green lines: physical revolute axes</li>
      <li>Purple: virtual spherical axes</li>
      <li>Dashed orange: quotiented terminal roll</li>
      <li>Selected axes also distinguished by label weight, not color alone</li>
    </ul>
  </aside>
</main>
<script>window.PROBE_SCENE = {payload};</script>
<script>{_VIEWER_JS}</script>
</body>
</html>
"""


_BROWSER_JS = r"""
(function(){
  const bundle = window.PROBE_BUNDLE;
  const selParent = document.getElementById("parent");
  const selS = document.getElementById("s");
  const selU1 = document.getElementById("u1");
  const selU2 = document.getElementById("u2");
  const chkArm = document.getElementById("arm");
  const chkUnsel = document.getElementById("unsel");
  const chkCenters = document.getElementById("centers");
  const chkOrtho = document.getElementById("ortho");
  const meta = document.getElementById("meta");
  const candidates = bundle.candidates || [];
  const parents = [...new Set(candidates.map(c => c.pair_set))];

  parents.forEach(p => {
    const o = document.createElement("option"); o.value=p; o.textContent=p; selParent.appendChild(o);
  });

  function filtered() {
    return candidates.filter(c => c.pair_set === selParent.value);
  }

  function refillChoices() {
    const list = filtered();
    const fill = (el, key) => {
      const vals = [...new Set(list.map(c => c[key]))];
      const prev = el.value;
      el.innerHTML = "";
      vals.forEach(v => { const o=document.createElement("option"); o.value=v; o.textContent=v; el.appendChild(o); });
      if (vals.includes(prev)) el.value = prev;
    };
    fill(selS, "s_choice");
    fill(selU1, "u_first_choice");
    fill(selU2, "u_second_choice");
  }

  function currentCandidate() {
    return candidates.find(c =>
      c.pair_set === selParent.value &&
      c.s_choice === selS.value &&
      c.u_first_choice === selU1.value &&
      c.u_second_choice === selU2.value
    );
  }

  function applyQuery() {
    const q = new URLSearchParams(location.search);
    if (q.get("parent") && parents.includes(q.get("parent"))) selParent.value = q.get("parent");
    refillChoices();
    if (q.get("s")) selS.value = q.get("s");
    if (q.get("u1")) selU1.value = q.get("u1");
    if (q.get("u2")) selU2.value = q.get("u2");
  }

  function pushQuery() {
    const q = new URLSearchParams();
    q.set("parent", selParent.value);
    q.set("s", selS.value);
    q.set("u1", selU1.value);
    q.set("u2", selU2.value);
    history.replaceState(null, "", "?" + q.toString());
  }

  function render() {
    const c = currentCandidate();
    const scene = {
      scene_id: "browser",
      title: "Candidate browser",
      kind: "browser",
      disclaimer: bundle.disclaimer || "Visual probe only.",
      fk: bundle.fk,
      arm_opacity: chkArm.checked ? 0.3 : 0.0,
      show_joint_centers: chkCenters.checked,
      show_unselected_axes: chkUnsel.checked,
      camera: { orthographic: chkOrtho.checked },
      closure: bundle.closure,
      candidate: c || null,
      notes: c ? [
        "candidate RRRR axis tuple (not certified)",
        c.candidate_id,
        "topology " + c.topology,
      ] : ["No candidate selected"],
    };
    window.PROBE_SCENE = scene;
    meta.textContent = c ? JSON.stringify({
      candidate_id: c.candidate_id,
      topology: c.topology,
      pair_set: c.pair_set,
      provenance: c.axes.map(a => a.role + ":" + a.source_id)
    }, null, 2) : "none";
    pushQuery();
    // re-exec viewer by dispatching resize after replacing script state
    const canvas = document.getElementById("view");
    canvas.replaceWith(canvas.cloneNode(true));
    const s = document.createElement("script");
    s.textContent = window.PROBE_VIEWER_SRC;
    document.body.appendChild(s);
    s.remove();
  }

  function step(delta) {
    const list = filtered();
    if (!list.length) return;
    let idx = list.findIndex(c => c.candidate_id === (currentCandidate()||{}).candidate_id);
    if (idx < 0) idx = 0;
    idx = (idx + delta + list.length) % list.length;
    const c = list[idx];
    selS.value = c.s_choice; selU1.value = c.u_first_choice; selU2.value = c.u_second_choice;
    render();
  }

  selParent.addEventListener("change", () => { refillChoices(); render(); });
  [selS, selU1, selU2, chkArm, chkUnsel, chkCenters, chkOrtho].forEach(el => el.addEventListener("change", render));
  document.getElementById("prev").addEventListener("click", () => step(-1));
  document.getElementById("next").addEventListener("click", () => step(1));

  window.PROBE_VIEWER_SRC = document.getElementById("viewer-src").textContent;
  applyQuery();
  refillChoices();
  render();
})();
"""


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_scene_html(path: Path, scene: dict[str, Any]) -> SceneRecord:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_html_page(scene["title"], scene), encoding="utf-8")
    return SceneRecord(
        scene_id=str(scene["scene_id"]),
        title=str(scene["title"]),
        path=str(path),
        kind=str(scene.get("kind", "scene")),
        notes=tuple(str(n) for n in scene.get("notes", ())),
    )


def write_contact_sheet(path: Path, candidates: list[dict[str, Any]], fk: dict[str, Any]) -> None:
    """Export a static contact sheet with one thumbnail block per candidate."""
    cards: list[str] = []
    for i, c in enumerate(candidates):
        scene = {
            "scene_id": c["candidate_id"],
            "title": c["candidate_id"],
            "kind": "contact",
            "disclaimer": "candidate RRRR axis tuple — visual screening only",
            "fk": fk,
            "arm_opacity": 0.15,
            "candidate": c,
            "camera": {"orthographic": True},
            "notes": [c["topology"], c["pair_set"]],
        }
        # Each card uses its own mini canvas via iframe-like inline viewer with unique id
        payload = json.dumps(scene)
        cards.append(
            f"""
<section class="card">
  <h3 class="mono">{c["candidate_id"]}</h3>
  <p>{c["topology"]} · {c["pair_set"]} · S={c["s_choice"]} · U1={c["u_first_choice"]} · U2={c["u_second_choice"]} · R{c["remaining_r"]}</p>
  <canvas id="c{i}" width="360" height="260"></canvas>
  <script>
  (function(){{
    const data = {payload};
    const canvas = document.getElementById("c{i}");
    const ctx = canvas.getContext("2d");
    const yaw=0.7, pitch=0.4, dist=1.9;
    function rotY(p,a){{const c=Math.cos(a),s=Math.sin(a);return[c*p[0]+s*p[2],p[1],-s*p[0]+c*p[2]];}}
    function rotX(p,a){{const c=Math.cos(a),s=Math.sin(a);return[p[0],c*p[1]-s*p[2],s*p[1]+c*p[2]];}}
    function project(p){{let q=rotY(p,yaw);q=rotX(q,pitch);const f=180;return[canvas.width/2+q[0]*f,canvas.height/2-q[1]*f];}}
    function line(a,b,col){{const pa=project(a),pb=project(b);ctx.beginPath();ctx.strokeStyle=col;ctx.lineWidth=2;ctx.moveTo(pa[0],pa[1]);ctx.lineTo(pb[0],pb[1]);ctx.stroke();}}
    function axis(ax,L,col){{const p=ax.point,d=ax.direction;line([p[0]-d[0]*L,p[1]-d[1]*L,p[2]-d[2]*L],[p[0]+d[0]*L,p[1]+d[1]*L,p[2]+d[2]*L],col);}}
    ctx.fillStyle="#f7f5f1"; ctx.fillRect(0,0,canvas.width,canvas.height);
    const L=(data.fk&&data.fk.axis_length)||0.28;
    (data.fk.links||[]).forEach(l=>line(l.start,l.end,"rgba(0,0,0,0.2)"));
    (data.candidate.axes||[]).forEach((ax,idx)=>axis(ax.axis,L,["#6a1b9a","#0b6e4f","#2e7d32","#1565c0"][idx]||"#333"));
    ctx.fillStyle="#222"; ctx.font="11px monospace"; ctx.fillText(data.title, 8, 14);
  }})();
  </script>
</section>
"""
        )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Candidate contact sheet</title>
<style>
body{{font-family:sans-serif;background:#efece6;margin:1rem;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:1rem;}}
.card{{background:#f7f5f1;border:1px solid #cfc8bb;padding:.75rem;}}
.mono{{font-family:ui-monospace,monospace;font-size:.8rem;word-break:break-all;}}
.disclaimer{{background:#fff3cd;padding:.5rem;margin-bottom:1rem;}}
</style></head><body>
<div class="disclaimer">{DISCLAIMER} Candidate RRRR tuples are coordinate-dependent and not certified spherical four-bars.</div>
<div class="grid">
{''.join(cards)}
</div>
</body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def write_index_browser(path: Path, bundle: dict[str, Any]) -> None:
    """Write the interactive static candidate browser."""
    bundle = {
        **bundle,
        "disclaimer": DISCLAIMER,
    }
    payload = json.dumps(bundle)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Aligned terminal-roll visual probe</title>
<style>{_SCENE_CSS}
.controls label {{ display:block; margin:.35rem 0; }}
.controls button {{ margin-right:.35rem; margin-top:.5rem; }}
pre {{ white-space:pre-wrap; background:#fff; border:1px solid #ddd; padding:.5rem; max-height:220px; overflow:auto; }}
</style>
</head>
<body>
<header>
  <h1>Aligned terminal-roll visual probe</h1>
  <div class="disclaimer">{DISCLAIMER}</div>
</header>
<main>
  <div id="view-wrap"><canvas id="view"></canvas></div>
  <aside class="controls">
    <h2>Selectors</h2>
    <label>Parent <select id="parent"></select></label>
    <label>S axis <select id="s"></select></label>
    <label>U1 axis <select id="u1"></select></label>
    <label>U2 axis <select id="u2"></select></label>
    <label><input type="checkbox" id="arm" checked/> Show physical arm</label>
    <label><input type="checkbox" id="unsel" checked/> Show unselected axes</label>
    <label><input type="checkbox" id="centers" checked/> Show joint centers</label>
    <label><input type="checkbox" id="ortho"/> Orthographic camera</label>
    <div>
      <button type="button" id="prev">Previous</button>
      <button type="button" id="next">Next</button>
    </div>
    <h2>Provenance</h2>
    <pre id="meta" class="mono"></pre>
  </aside>
</main>
<script>window.PROBE_BUNDLE = {payload};</script>
<script type="text/plain" id="viewer-src">{_VIEWER_JS}</script>
<script>{_BROWSER_JS}</script>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def write_manifest(path: Path, manifest: Manifest) -> None:
    write_json(
        path,
        {
            "project": manifest.project,
            "disclaimer": manifest.disclaimer,
            "config_name": manifest.config_name,
            "output_dir": manifest.output_dir,
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "title": s.title,
                    "path": s.path,
                    "kind": s.kind,
                    "notes": list(s.notes),
                }
                for s in manifest.scenes
            ],
            "data_files": list(manifest.data_files),
        },
    )
