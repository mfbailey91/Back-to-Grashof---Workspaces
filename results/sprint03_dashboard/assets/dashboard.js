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

  function renderSprint4() {
    const stats = document.getElementById("gate2-stats");
    const table = document.getElementById("solver-table");
    if (!data.gate2) return;
    const g = data.gate2;
    if (stats) {
      stats.innerHTML = `
        <div class="stat"><div class="k">Gate 2</div><div class="v">${g.gate2_pass ? '<span class="badge exact">PASS</span>' : '<span class="badge invalid">FAIL</span>'}</div></div>
        <div class="stat"><div class="k">Coverage</div><div class="v mono">${fmt(g.coverage)}</div></div>
        <div class="stat"><div class="k">Components</div><div class="v mono">${g.component_count}</div></div>
        <div class="stat"><div class="k">Eligible solve</div><div class="v mono">${fmt(g.eligible_solve_rate)}</div></div>
      `;
    }
    if (table && data.solver_counts) {
      const s = data.solver_counts;
      table.innerHTML = `
        <table>
          <thead><tr><th>Status</th><th>Count</th><th>Meaning</th></tr></thead>
          <tbody>
            <tr><td><span class="badge exact">solved</span></td><td class="mono">${s.solved}</td><td>Residual below tolerance</td></tr>
            <tr><td><span class="badge invalid">unreachable</span></td><td class="mono">${s.unreachable}</td><td>Geometric precheck failed</td></tr>
            <tr><td><span class="badge approximate">solver_failed</span></td><td class="mono">${s.solver_failed}</td><td>Eligible but optimizer missed</td></tr>
          </tbody>
        </table>`;
    }
  }

  function renderSprint5() {
    const stats = document.getElementById("gate-stats");
    const table = document.getElementById("experiment-table");
    if (!data.gates) return;
    const g = data.gates;
    if (stats) {
      stats.innerHTML = `
        <div class="stat"><div class="k">Gate 3 precision</div><div class="v mono">${g.gate3_crank_precision == null ? "—" : fmt(g.gate3_crank_precision)}</div></div>
        <div class="stat"><div class="k">Gate 3 recall</div><div class="v mono">${g.gate3_crank_recall == null ? "—" : fmt(g.gate3_crank_recall)}</div></div>
        <div class="stat"><div class="k">Gate 4 corr(ρ,err)</div><div class="v mono">${g.gate4_residual_error_correlation == null ? "—" : fmt(g.gate4_residual_error_correlation)}</div></div>
        <div class="stat"><div class="k">Gate 5 C stable</div><div class="v">${g.gate5_c_orientation_stable ? '<span class="badge exact">yes</span>' : '<span class="badge approximate">no/—</span>'}</div></div>
      `;
    }
    if (table && data.records) {
      table.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Arch</th><th>Spherical</th><th>ρ_C</th><th>Type</th>
              <th>Coverage</th><th>Outcome</th><th>Hypothesis</th>
            </tr>
          </thead>
          <tbody>
            ${data.records
              .map(
                (r) => `<tr>
                  <td class="mono">${r.architecture_id}</td>
                  <td>${badgeStatus(r.spherical_reduction_status)}</td>
                  <td class="mono">${fmt(r.concurrency_residual, 6)}</td>
                  <td class="mono">${r.linkage_type == null ? "—" : r.linkage_type}</td>
                  <td class="mono">${fmt(r.orientation_coverage)}</td>
                  <td>${r.prediction_outcome}</td>
                  <td>${r.analytical_prediction ? "candidate" : "no"}</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table>`;
    }
  }

  function renderSprint6() {
    const picker = document.getElementById("state-picker");
    const epsW = document.getElementById("eps-w-slider");
    const epsS = document.getElementById("eps-s-slider");
    const epsWVal = document.getElementById("eps-w-value");
    const epsSVal = document.getElementById("eps-s-value");
    const hint = document.getElementById("filter-hint");
    const records = data.records || [];
    const epsGrid = data.epsilon_grid || [0, 0.025, 0.05, 0.1, 0.2];
    if (!picker || !records.length) return;

    function epsAt(slider) {
      const idx = Number(slider && slider.value) || 0;
      return epsGrid[Math.min(Math.max(idx, 0), epsGrid.length - 1)];
    }

    function near(a, b, tol = 1e-9) {
      return Math.abs(Number(a) - Number(b)) <= tol;
    }

    function filtered() {
      const ew = epsAt(epsW);
      const es = epsAt(epsS);
      return records.filter((r) => {
        const op = r.offset_parameters || {};
        if (r.architecture_id === "B") return near(op.epsilon_w, ew);
        if (r.architecture_id === "C") return near(op.epsilon_s, es);
        return true;
      });
    }

    function paintPicker() {
      const rows = filtered();
      const prev = picker.value;
      picker.innerHTML = rows
        .map(
          (r) =>
            `<option value="${r.record_id}">${r.record_id} · ${r.architecture_id} · ${r.prediction_outcome}</option>`
        )
        .join("");
      if (hint) {
        hint.textContent = `${rows.length} / ${records.length} records visible (A always; B by εw; C by εs)`;
      }
      if ([...picker.options].some((o) => o.value === prev)) {
        picker.value = prev;
      } else if (picker.options.length) {
        picker.selectedIndex = 0;
      }
      paintState();
    }

    function recordById(id) {
      return records.find((r) => r.record_id === id) || filtered()[0] || records[0];
    }

    function paintState() {
      const r = recordById(picker.value);
      if (!r) return;
      const op = r.offset_parameters || {};

      const badges = document.getElementById("outcome-badges");
      if (badges) {
        badges.innerHTML = `
          <div class="stat"><div class="k">Outcome</div><div class="v">${r.prediction_outcome}</div></div>
          <div class="stat"><div class="k">Regional</div><div class="v">${badgeStatus(r.regional_reduction_status)}</div></div>
          <div class="stat"><div class="k">Spherical</div><div class="v">${badgeStatus(r.spherical_reduction_status)}</div></div>
          <div class="stat"><div class="k">ρ_C</div><div class="v mono">${fmt(r.concurrency_residual, 6)}</div></div>
        `;
      }

      const arm = document.getElementById("view-arm");
      const armCap = document.getElementById("view-arm-caption");
      if (arm && r.arm_figure) {
        arm.src = r.arm_figure;
        if (armCap) {
          armCap.textContent = `Arch ${r.architecture_id} · εw=${fmt(op.epsilon_w, 3)} · εs=${fmt(op.epsilon_s, 3)}`;
        }
      }

      const pos = document.getElementById("view-position");
      if (pos) {
        const p = r.position || [];
        const q = r.joint_configuration_seed || [];
        pos.innerHTML = `
          <table>
            <tbody>
              <tr><th>Branch</th><td class="mono">${r.position_branch_id || "—"}</td></tr>
              <tr><th>Position</th><td class="mono">${p.map((v) => fmt(v)).join(", ")}</td></tr>
              <tr><th>Seed q</th><td class="mono">${q.map((v) => fmt(v)).join(", ")}</td></tr>
              <tr><th>Offsets</th><td class="mono">εw=${fmt(op.epsilon_w, 3)}, εs=${fmt(op.epsilon_s, 3)}, Lt=${fmt(op.Lt, 3)}</td></tr>
            </tbody>
          </table>`;
      }

      const ti = document.getElementById("view-ti");
      if (ti) {
        ti.innerHTML = `
          <table>
            <tbody>
              <tr><th>Type</th><td class="mono">${r.linkage_type == null ? "—" : r.linkage_type}</td></tr>
              <tr><th>T₁…T₄</th><td class="mono">${[r.T1, r.T2, r.T3, r.T4].map((v) => fmt(v)).join(", ")}</td></tr>
              <tr><th>Signs</th><td class="mono">${r.T_sign_tuple ? signText(r.T_sign_tuple) : "—"}</td></tr>
              <tr><th>Input / output</th><td>${r.input_motion_class} / ${r.output_motion_class}</td></tr>
              <tr><th>Hand (β)</th><td>${r.hand_link_motion_class}</td></tr>
              <tr><th>Angles αβγη</th><td class="mono">${
                r.spherical_link_angles
                  ? r.spherical_link_angles.map((v) => fmt(v)).join(", ")
                  : "withheld"
              }</td></tr>
            </tbody>
          </table>`;
      }

      const pred = document.getElementById("view-prediction");
      if (pred) {
        pred.innerHTML = `
          <table>
            <tbody>
              <tr><th>Analytical candidate</th><td>${r.analytical_prediction ? '<span class="badge hyp">yes</span>' : '<span class="badge no">no</span>'}</td></tr>
              <tr><th>Strict sampled dexterity</th><td>${r.strict_sampled_dexterity ? "true" : "false"}</td></tr>
              <tr><th>Outcome</th><td class="mono">${r.prediction_outcome}</td></tr>
              <tr><th>Eligible solve rate</th><td class="mono">${fmt((r.extras || {}).eligible_solve_rate)}</td></tr>
            </tbody>
          </table>`;
      }

      const status = document.getElementById("view-status");
      if (status) {
        status.innerHTML = `
          <p>${badgeStatus(r.regional_reduction_status)} regional · ${badgeStatus(r.spherical_reduction_status)} spherical</p>
          <p class="note">Regional reachable: ${r.regional_reachable ? "yes" : "no"} · residual shown whenever not exact.</p>
          <p class="mono">ρ_C = ${fmt(r.concurrency_residual, 6)}</p>`;
      }

      const cov = document.getElementById("view-coverage");
      if (cov) {
        cov.innerHTML = `
          <div class="stat-row">
            <div class="stat"><div class="k">Coverage</div><div class="v mono">${fmt(r.orientation_coverage)}</div></div>
            <div class="stat"><div class="k">Components</div><div class="v mono">${r.orientation_component_count}</div></div>
            <div class="stat"><div class="k">Solved</div><div class="v mono">${r.solved_count}</div></div>
            <div class="stat"><div class="k">Unreachable</div><div class="v mono">${r.unreachable_count}</div></div>
            <div class="stat"><div class="k">Solver failed</div><div class="v mono">${r.solver_failed_count}</div></div>
          </div>`;
      }

      const connCap = document.getElementById("view-connectivity-caption");
      if (connCap) {
        connCap.textContent = `Record coverage=${fmt(r.orientation_coverage)} · components=${r.orientation_component_count}`;
      }
    }

    if (epsWVal) epsWVal.textContent = String(epsAt(epsW));
    if (epsSVal) epsSVal.textContent = String(epsAt(epsS));
    if (epsW) {
      epsW.addEventListener("input", () => {
        if (epsWVal) epsWVal.textContent = String(epsAt(epsW));
        paintPicker();
      });
    }
    if (epsS) {
      epsS.addEventListener("input", () => {
        if (epsSVal) epsSVal.textContent = String(epsAt(epsS));
        paintPicker();
      });
    }
    picker.addEventListener("change", paintState);

    const gates = document.getElementById("gate-stats");
    if (gates && data.gates) {
      const g = data.gates;
      gates.innerHTML = `
        <div class="stat"><div class="k">Gate 3 precision</div><div class="v mono">${g.gate3_crank_precision == null ? "—" : fmt(g.gate3_crank_precision)}</div></div>
        <div class="stat"><div class="k">Gate 3 recall</div><div class="v mono">${g.gate3_crank_recall == null ? "—" : fmt(g.gate3_crank_recall)}</div></div>
        <div class="stat"><div class="k">Gate 4 corr</div><div class="v mono">${g.gate4_residual_error_correlation == null ? "—" : fmt(g.gate4_residual_error_correlation)}</div></div>
        <div class="stat"><div class="k">Gate 5 C stable</div><div class="v">${g.gate5_c_orientation_stable ? '<span class="badge exact">yes</span>' : '<span class="badge approximate">no/—</span>'}</div></div>
      `;
    }

    paintPicker();
  }

  if (data.sprint === 0) renderSprint0();
  if (data.sprint === 1) renderSprint1();
  if (data.sprint === 2) renderSprint2();
  if (data.sprint === 3) renderSprint3();
  if (data.sprint === 4) renderSprint4();
  if (data.sprint === 5) renderSprint5();
  if (data.sprint === 6) renderSprint6();
})();
