(() => {
  const raw = document.getElementById("dashboard-data");
  if (!raw) return;
  const data = JSON.parse(raw.textContent || "{}");

  function signText(signs) {
    return signs.map((s) => (s > 0 ? "+" : "−")).join(" ");
  }

  function fmt(n, digits = 3) {
    if (typeof n !== "number" || Number.isNaN(n)) return "—";
    if (Math.abs(n) > 0 && Math.abs(n) < 1e-4) return n.toExponential(2);
    return n.toFixed(digits);
  }

  function badgeStatus(status) {
    const cls = status === "exact" ? "exact" : status === "approximate" ? "approximate" : "invalid";
    return `<span class="badge ${cls}">${status}</span>`;
  }

  function renderSprint0() {
    const tableHost = document.getElementById("type-table");
    const fixtureHost = document.getElementById("fixture-table");
    const workedHost = document.getElementById("worked-stats");
    const filter = document.getElementById("type-filter");
    if (!tableHost || !data.types) return;

    if (workedHost && data.worked_closure) {
      const w = data.worked_closure;
      workedHost.innerHTML = `
        <div class="stat"><div class="k">Type</div><div class="v">${w.type} · ${w.name}</div></div>
        <div class="stat"><div class="k">Hand link β</div><div class="v">${w.hand_link_motion_class}</div></div>
        <div class="stat"><div class="k">Grashof family</div><div class="v">${w.grashof_family}</div></div>
        <div class="stat"><div class="k">Dexterity hypothesis</div><div class="v">${w.dexterity_candidate_hypothesis ? "candidate" : "not candidate"}</div></div>
      `;
    }

    function paintTypes(mode) {
      const rows = data.types.filter((t) => {
        if (mode === "candidates") return t.dexterity_candidate_hypothesis;
        if (mode === "wrap") return t.wrap_around;
        if (mode === "plain") return !t.wrap_around;
        return true;
      });
      tableHost.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Type</th><th>Name</th><th>Signs</th><th>Input</th><th>Output / hand</th><th>Wrap</th><th>Hypothesis</th>
            </tr>
          </thead>
          <tbody>
            ${rows
              .map(
                (t) => `
              <tr class="${t.dexterity_candidate_hypothesis ? "candidate" : ""}">
                <td class="mono">${t.type}</td>
                <td>${t.name}</td>
                <td class="mono">${signText(t.signs)}</td>
                <td>${t.input}</td>
                <td>${t.output}</td>
                <td>${t.wrap_around ? "yes" : "no"}</td>
                <td>${t.dexterity_candidate_hypothesis ? '<span class="badge hyp">★ crank hand</span>' : '<span class="badge no">—</span>'}</td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>`;
    }

    if (filter) {
      filter.addEventListener("change", () => paintTypes(filter.value));
      paintTypes(filter.value);
    } else {
      paintTypes("all");
    }

    if (fixtureHost && data.fixtures) {
      fixtureHost.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Label</th><th>Type</th><th>T1…T4</th><th>Input</th><th>Hand</th><th>Hypothesis</th>
            </tr>
          </thead>
          <tbody>
            ${data.fixtures
              .map(
                (f) => `
              <tr class="${f.dexterity_candidate_hypothesis ? "candidate" : ""}">
                <td class="mono">${f.label}</td>
                <td>${f.type}</td>
                <td class="mono">${f.T.map((v) => fmt(v)).join(", ")}</td>
                <td>${f.input_motion_class}</td>
                <td>${f.hand_link_motion_class}</td>
                <td>${f.dexterity_candidate_hypothesis ? "yes" : "no"}</td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>`;
    }
  }

  function renderSprint1() {
    const archHost = document.getElementById("arch-cards");
    const sweepB = document.getElementById("sweep-b");
    const sweepC = document.getElementById("sweep-c");
    const buttons = document.querySelectorAll("[data-arch-filter]");
    if (!archHost || !data.architectures) return;

    function paint(filterId) {
      const rows = data.architectures.filter((a) => filterId === "all" || a.id.startsWith(filterId));
      archHost.innerHTML = rows
        .map((a) => {
          const status = (a.report && a.report.spherical_status) || "—";
          const rho = (a.report && a.report.concurrency_residual_rho) || "—";
          return `
          <article class="panel arch-card">
            <h3>${a.label} ${badgeStatus(status)}</h3>
            <p class="note">${a.note}</p>
            <figure>
              <img src="${a.figure}" alt="${a.label}" />
              <figcaption>ρ = ${rho}</figcaption>
            </figure>
          </article>`;
        })
        .join("");
    }

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        paint(btn.getAttribute("data-arch-filter") || "all");
      });
    });
    paint("all");

    if (sweepB && data.sweep_b) {
      sweepB.innerHTML = `
        <table>
          <thead><tr><th>εw</th><th>ρ_C</th><th>Status</th></tr></thead>
          <tbody>
            ${data.sweep_b
              .map(
                (r) => `<tr>
                  <td class="mono">${fmt(r.epsilon_w, 3)}</td>
                  <td class="mono">${fmt(r.rho, 6)}</td>
                  <td>${badgeStatus(r.status)}</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table>`;
    }
    if (sweepC && data.sweep_c) {
      sweepC.innerHTML = `
        <table>
          <thead><tr><th>εs</th><th>d(z1,z2)</th><th>ρ_C</th><th>Status</th></tr></thead>
          <tbody>
            ${data.sweep_c
              .map(
                (r) => `<tr>
                  <td class="mono">${fmt(r.epsilon_s, 3)}</td>
                  <td class="mono">${fmt(r.z1_z2_distance, 6)}</td>
                  <td class="mono">${fmt(r.rho, 6)}</td>
                  <td>${badgeStatus(r.status)}</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table>`;
    }
  }

  function renderSprint2() {
    const stats = document.getElementById("reduction-stats");
    const table = document.getElementById("reduction-table");
    if (!data.reductions) return;

    if (stats) {
      const a = data.reductions.find((r) => r.architecture_id === "A") || data.reductions[0];
      stats.innerHTML = `
        <div class="stat"><div class="k">Arch A spherical</div><div class="v">${badgeStatus(a.spherical_status)}</div></div>
        <div class="stat"><div class="k">ρ_C</div><div class="v mono">${fmt(a.concurrency_residual, 6)}</div></div>
        <div class="stat"><div class="k">ρ_w</div><div class="v mono">${fmt(a.rho_w)}</div></div>
        <div class="stat"><div class="k">Spherical type</div><div class="v">${a.linkage_type != null ? a.linkage_type : "—"}</div></div>
      `;
    }

    if (table) {
      table.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Arch</th><th>Regional</th><th>Spherical</th><th>ρ_C</th>
              <th>ρ_w</th><th>Angles</th><th>Notes</th>
            </tr>
          </thead>
          <tbody>
            ${data.reductions
              .map(
                (r) => `<tr>
                  <td class="mono">${r.architecture_id}</td>
                  <td>${badgeStatus(r.regional_status)}</td>
                  <td>${badgeStatus(r.spherical_status)}</td>
                  <td class="mono">${fmt(r.concurrency_residual, 6)}</td>
                  <td class="mono">${fmt(r.rho_w)}</td>
                  <td class="mono">${
                    r.spherical_angles
                      ? r.spherical_angles.map((v) => fmt(v)).join(", ")
                      : "withheld"
                  }</td>
                  <td>${r.notes || "—"}</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table>`;
    }
  }

  function renderSprint3() {
    const stats = document.getElementById("prediction-stats");
    const detail = document.getElementById("prediction-detail");
    const toggle = document.getElementById("hand-link-toggle");
    const summary = document.getElementById("type-map-summary");
    const mapTable = document.getElementById("type-map-table");
    if (!data.predictions) return;

    function paintPrediction(key) {
      const pred = data.predictions[key] || data.predictions.beta;
      if (stats) {
        stats.innerHTML = `
          <div class="stat"><div class="k">Type</div><div class="v">${pred.linkage_type} · ${pred.linkage_name}</div></div>
          <div class="stat"><div class="k">Hand (${pred.hand_orientation_link})</div><div class="v">${pred.hand_link_motion_class}</div></div>
          <div class="stat"><div class="k">Family</div><div class="v">${pred.grashof_family}</div></div>
          <div class="stat"><div class="k">Hypothesis</div><div class="v">${
            pred.dexterity_candidate_hypothesis
              ? '<span class="badge hyp">candidate</span>'
              : '<span class="badge no">not candidate</span>'
          }</div></div>
        `;
      }
      if (detail) {
        detail.innerHTML = `
          <table>
            <tbody>
              <tr><th>Status</th><td>${badgeStatus(pred.reduction_status)} · ρ_C=${fmt(pred.concurrency_residual, 6)}</td></tr>
              <tr><th>T₁…T₄</th><td class="mono">${[pred.T1, pred.T2, pred.T3, pred.T4].map((v) => fmt(v)).join(", ")}</td></tr>
              <tr><th>Signs</th><td class="mono">${pred.sign_tuple ? signText(pred.sign_tuple) : "—"}</td></tr>
              <tr><th>Product</th><td class="mono">${fmt(pred.T_product)} <span class="badge no">≠ dexterity</span></td></tr>
              <tr><th>Input / output</th><td>${pred.input_motion_class} / ${pred.output_motion_class}</td></tr>
              <tr><th>Angles (α,β,γ,η)</th><td class="mono">${
                pred.spherical_link_angles
                  ? pred.spherical_link_angles.map((v) => fmt(v)).join(", ")
                  : "withheld"
              }</td></tr>
            </tbody>
          </table>`;
      }
    }

    if (toggle) {
      toggle.addEventListener("change", () => paintPrediction(toggle.value));
      paintPrediction(toggle.value);
    } else {
      paintPrediction("beta");
    }

    if (summary && data.type_map_summary) {
      const s = data.type_map_summary;
      summary.innerHTML = `
        <div class="stat"><div class="k">Samples</div><div class="v">${s.n_samples}</div></div>
        <div class="stat"><div class="k">Distinct types</div><div class="v">${s.n_types}</div></div>
        <div class="stat"><div class="k">Hypothesis hits</div><div class="v">${s.n_candidates}</div></div>
        <div class="stat"><div class="k">Hand link</div><div class="v">${s.hand_orientation_link}</div></div>
      `;
    }

    if (mapTable && data.type_counts) {
      mapTable.innerHTML = `
        <table>
          <thead><tr><th>Type</th><th>Count</th><th>Hypothesis present</th></tr></thead>
          <tbody>
            ${data.type_counts
              .map(
                (r) => `<tr class="${r.has_candidate ? "candidate" : ""}">
                  <td class="mono">${r.type}</td>
                  <td class="mono">${r.count}</td>
                  <td>${r.has_candidate ? "yes" : "no"}</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table>`;
    }
  }

  if (data.sprint === 0) renderSprint0();
  if (data.sprint === 1) renderSprint1();
  if (data.sprint === 2) renderSprint2();
  if (data.sprint === 3) renderSprint3();
})();
