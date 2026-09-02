/* Presentation renderer. Does not assign scientific statuses. */
(function () {
  "use strict";

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function dollarsToParen(s) {
    const t = String(s);
    let out = "";
    let inMath = false;
    for (let i = 0; i < t.length; i += 1) {
      if (t[i] === "$") {
        out += inMath ? "\\)" : "\\(";
        inMath = !inMath;
      } else {
        out += t[i];
      }
    }
    return out;
  }

  function asInline(tex) {
    if (!tex) return "";
    const t = dollarsToParen(String(tex).trim());
    if (!t) return "";
    if (t.includes("\\(") || t.includes("\\[")) return esc(t);
    if (/\\[a-zA-Z]/.test(t) || /[_^]/.test(t)) return "\\(" + esc(t) + "\\)";
    return esc(t);
  }

  function asDisplay(tex) {
    if (!tex) return "";
    const t = dollarsToParen(String(tex).trim());
    if (!t) return "";
    if (t.startsWith("\\[")) return esc(t);
    return "\\[" + esc(t) + "\\]";
  }

  function badge(status) {
    const cls = String(status || "").replace(/[^A-Z_]/g, "") || "UNKNOWN";
    return '<span class="badge ' + cls + '">' + esc(status) + "</span>";
  }

  function nodeClass(status) {
    return "node " + String(status || "").replace(/[^A-Z_]/g, "");
  }

  function relById(data, id) {
    return data.relations.find(function (r) { return r.id === id; });
  }

  function typeset(root) {
    if (window.MathJax && window.MathJax.typesetPromise) {
      return window.MathJax.typesetPromise(root ? [root] : undefined).catch(function (err) {
        console.warn("MathJax typeset failed", err);
      });
    }
    return Promise.resolve();
  }

  function renderFeaturedTable(data) {
    const rows = data.featured_overview.map(function (row) {
      return (
        "<tr>" +
        '<td><a href="#rel-' + esc(row.relation_id) + '">' + esc(row.public_display) + "</a></td>" +
        "<td>" + asInline(row.what_happens) + "</td>" +
        "<td>" + esc(row.evidence) + "</td>" +
        "<td>" + badge(row.final_status) + "</td>" +
        "</tr>"
      );
    }).join("");
    return (
      '<div class="table-wrap"><table class="overview">' +
      "<thead><tr><th>Eq. relation</th><th>What happens</th><th>Evidence</th><th>Final status</th></tr></thead>" +
      "<tbody>" + rows + "</tbody></table></div>"
    );
  }

  function stepNodes(step, which) {
    const list = which === "from" ? step.from : step.to;
    const fallback = which === "from" ? step.public_display.split("→")[0] : step.public_display;
    const labels = (list && list.length) ? list : [fallback.trim()];
    return labels.map(function (lab) {
      return (
        '<div class="' + nodeClass(step.final_status) + '">' +
        '<span class="eq">' + esc(lab) + "</span>" +
        (step.math_summary_tex ? '<span class="math">' + asInline(step.math_summary_tex) + "</span>" : "") +
        "</div>"
      );
    }).join("");
  }

  function renderChain(chain) {
    const steps = chain.steps.map(function (step) {
      const cond = step.condition_tex
        ? '<span class="cond">' + asInline(step.condition_tex) + "</span>"
        : "";
      const fromLabs = (step.from && step.from.length) ? step.from : [];
      const toLabs = (step.to && step.to.length) ? step.to : [];
      const singleton = fromLabs.join("|") === toLabs.join("|");
      const btn = (
        '<button type="button" class="edge-btn" data-open="rel-' + esc(step.relation_id) + '">' +
        '<span class="move">' + esc(step.move) + "</span>" +
        cond +
        badge(step.final_status) +
        "</button>"
      );
      if (singleton) {
        return (
          '<div class="flow-step">' +
          '<div class="nodes-row">' + stepNodes(step, "to") + "</div>" +
          btn +
          "</div>"
        );
      }
      return (
        '<div class="flow-step">' +
        '<div class="nodes-row">' + stepNodes(step, "from") + "</div>" +
        btn +
        '<div class="arrow" aria-hidden="true">↓</div>' +
        '<div class="nodes-row">' + stepNodes(step, "to") + "</div>" +
        "</div>"
      );
    }).join("");
    const body = (chain.layout === "list")
      ? '<div class="rel-list">' + chain.steps.map(function (step) {
          return (
            '<button type="button" class="rel-row" data-open="rel-' + esc(step.relation_id) + '" ' +
            'data-status="' + esc(step.final_status) + '" data-section="' + esc(chain.section) + '">' +
            '<span class="eq">' + esc(step.public_display) + "</span>" +
            '<span class="cue">' + asInline(step.math_summary_tex) + "</span>" +
            badge(step.final_status) +
            "</button>"
          );
        }).join("") + "</div>"
      : '<div class="flow">' + steps + "</div>";
    return (
      '<article class="chain" id="chain-' + esc(chain.id) + '" data-section="' + esc(chain.section) + '">' +
      '<h4 class="chain-title">' + asInline(chain.title) + "</h4>" +
      '<p class="chain-summary">' + asInline(chain.summary) + "</p>" +
      body +
      "</article>"
    );
  }

  function residualBlock(rel) {
    const d = rel.direct || {};
    if (rel.final_status === "CERTIFIED_BY_RULE" || d.verdict === "N/A") {
      return "<p>No parent equality residual is compiled. The checked object, if any, is a local identity plus a declared rule — not "
        + asInline("E_{\\mathrm{lhs}}-E_{\\mathrm{rhs}}")
        + " of a global integral.</p>";
    }
    if (d.verdict === "UNKNOWN" || rel.final_status === "UNKNOWN_REMAINDER") {
      return "<p>No executable residual is compiled for this remainder or limit claim. Direct check: UNKNOWN. That is not a refutation.</p>";
    }
    const fromN = (rel.public_from || []).length;
    const rhsZero = rel.after && (rel.after.tex === "0" || rel.after.encoding === "0");
    let html;
    if (fromN > 1 && rhsZero) {
      html = "<p>Compiled obligation (multi-parent). Frozen right-hand encoding is 0. This is not a single-equation before/after:</p>" +
        asDisplay("R=E_{\\mathrm{lhs}}");
    } else {
      html = "<p>Compiled obligation for the claimed equality of two frozen encodings:</p>" +
        asDisplay("R=E_{\\mathrm{lhs}}-E_{\\mathrm{rhs}}");
    }
    if (d.verdict === "ZERO") {
      html += "<p>Exact residual:</p>" + asDisplay("R=0");
      return html;
    }
    if (d.residual_tex) {
      html += "<p>Exact residual (direct, as compiled):</p><div class='math-scroll'>" + asDisplay("R=" + d.residual_tex) + "</div>";
      if (d.residual_tex_full && d.residual_tex_full !== d.residual_tex) {
        html +=
          '<p><button type="button" class="linkish" data-toggle-residual="' + esc(rel.id) + '">Show full residual</button></p>' +
          '<div class="full-residual math-scroll" id="full-res-' + esc(rel.id) + '" hidden>' +
          asDisplay(d.residual_tex_full) +
          "</div>";
      }
    } else {
      html += "<p>The frozen record marks this direct check " + esc(d.verdict) +
        "; a compact TeX projection of the residual is not available. See technical provenance for encodings.</p>";
    }
    return html;
  }

  function substitutionDiagram(rel) {
    if (rel.final_status !== "ZERO_UNDER_SUBSTITUTION") return "";
    const condTex = rel.condition && rel.condition.tex ? rel.condition.tex : rel.condition.text;
    return (
      '<div class="check-pair">' +
      '<div class="check direct"><div class="k">Direct check</div>' +
      asDisplay("R_{\\mathrm{direct}}\\neq 0") +
      "<p>" + badge(rel.direct.verdict) + "</p></div>" +
      '<div class="pluscol">+</div>' +
      '<div class="check cond"><div class="k">Author-used identity</div>' +
      (condTex ? asDisplay(String(condTex).replace(/^substitute /i, "")) : "<p>" + esc(rel.condition.text) + "</p>") +
      "</div></div>" +
      '<p style="text-align:center;margin:0.2rem 0;">↓</p>' +
      '<div class="check cond"><div class="k">Conditional check</div>' +
      asDisplay("R_{\\mathrm{cond}}=0") +
      "<p>" + badge(rel.conditional.verdict) + "</p>" +
      "<p>This direct NONZERO is not by itself an error in the paper.</p></div>"
    );
  }

  function ruleBox(rel) {
    if (!rel.rule_certification) return "";
    const rc = rel.rule_certification;
    const helperMath = "<p><strong>Local identity</strong> (helper, not a numbered-equation row):</p>" +
      (rc.local_identity.indexOf("\\(") >= 0 ? rc.local_identity : asDisplay(rc.local_identity));
    return (
      '<div class="rule-box">' +
      "<p><strong>Claimed move:</strong> " + esc(rc.claimed_move) + "</p>" +
      helperMath +
      "<p><strong>Local machine result:</strong> " + badge(rc.local_machine_result) +
      " <span class='count-note'>(copied from the parent frozen record; this page does not re-run the engine)</span></p>" +
      "<p><strong>Rule / domain:</strong> " + esc(rc.rule_domain.join(", ")) + "</p>" +
      "<p><strong>Parent status:</strong> " + badge(rc.parent_status) + "</p>" +
      '<p class="warn">The engine did not evaluate the global Brillouin-zone integral to ZERO. ' +
      "Do not read the child ZERO plus the rule as parent ZERO.</p>" +
      "</div>"
    );
  }

  function remainderBox(rel) {
    if (rel.final_status !== "UNKNOWN_REMAINDER") return "";
    const tex = rel.remainder_display_tex;
    return (
      '<div class="remainder-box">' +
      (tex ? "<div class='math-scroll'>" + asDisplay(tex) + "</div>" : "") +
      "<p>The author declares an asymptotic remainder. Finite coefficient identities may be checked separately. " +
      "No general remainder certificate is available in the frozen system.</p>" +
      "<p><strong>This is not a claim that the expansion is false.</strong> " +
      "It is a statement that the current evidence does not certify the enclosing remainder.</p>" +
      "</div>"
    );
  }

  function beforeAfter(rel) {
    let html = "";
    if (rel.before && rel.before.tex) {
      html += "<h4>Left encoding (frozen)</h4><div class='block math-scroll'>" + asDisplay(rel.before.tex) + "</div>";
    }
    if (rel.after && rel.after.tex) {
      html += "<h4>Right encoding (frozen)</h4><div class='block math-scroll'>" + asDisplay(rel.after.tex) + "</div>";
    }
    return html;
  }

  function techDrawer(rel) {
    const t = rel.technical_provenance || {};
    const dump = {
      internal_id: t.internal_id,
      regression: t.regression,
      claimed: t.claimed,
      parent_status_field: t.parent_status_field,
      engine: t.engine,
      software: t.software,
      frozen_left_encoding: t.frozen_left_encoding,
      frozen_right_encoding: t.frozen_right_encoding,
      frozen_subst_encoding: t.frozen_subst_encoding,
      results_direct: t.results_direct,
      results_conditional: t.results_conditional,
      results_final: t.results_final,
    };
    return (
      '<details class="tech"><summary>Technical provenance</summary>' +
      "<p>Internal identifiers are not the public equation numbers. " +
      "Encodings below are frozen machine strings, not a second verdict.</p>" +
      "<pre>" + esc(JSON.stringify(dump, null, 2)) + "</pre></details>"
    );
  }

  function renderEdge(rel) {
    const hay = [
      rel.public_display,
      rel.author_move,
      rel.final_status,
      rel.math_summary_tex,
      (rel.public_from || []).join(" "),
      (rel.public_to || []).join(" "),
      rel.role,
      rel.human_explanation,
      rel.why_direct_nonzero,
      rel.interpretation,
      (rel.condition && rel.condition.text) || "",
      (rel.condition && rel.condition.tex) || "",
      ((rel.author_source_anchor || {}).prose_paraphrase) || "",
      (rel.direct && rel.direct.residual_tex) || "",
    ].join(" ").toLowerCase();
    const why = rel.why_direct_nonzero
      ? "<h4>Why the direct check is NONZERO</h4><p>" + asInline(rel.why_direct_nonzero) + "</p>" +
        (rel.presentation_reason ? "<p>Presentation reason (not a machine verdict): " +
          '<span class="mono">' + esc(rel.presentation_reason) + "</span></p>" : "")
      : "";
    const condResidual = (rel.final_status === "ZERO_UNDER_SUBSTITUTION")
      ? "<h4>Conditional residual</h4>" + asDisplay("R_{\\mathrm{cond}}=\\left.R_{\\mathrm{direct}}\\right|_{\\text{source-grounded condition}}=0")
      : "";
    return (
      '<details class="edge ' + esc(rel.final_status) + '" id="rel-' + esc(rel.id) + '" ' +
      'data-status="' + esc(rel.final_status) + '" data-section="' + esc(rel.section) + '" data-hay="' + esc(hay) + '">' +
      "<summary><span><span class='sum-eq'>" + esc(rel.public_display) + "</span>" +
      "<span class='sum-move'>" + esc(rel.author_move) + "</span></span>" +
      badge(rel.final_status) + "</summary>" +
      '<div class="panel">' +
      "<h4>Role in the derivation</h4><p>" + asInline(rel.role) + "</p>" +
      "<h4>Source relation</h4><p>" + esc(rel.public_display) + "</p>" +
      "<h4>Author's move</h4><p>" + esc(rel.author_move) +
      (rel.math_summary_tex ? " — " + asInline(rel.math_summary_tex) : "") + "</p>" +
      "<h4>Source context</h4><p>" + asInline((rel.author_source_anchor || {}).prose_paraphrase) + "</p>" +
      "<p class='count-note'>" + esc((rel.author_source_anchor || {}).source || "") +
      (((rel.author_source_anchor || {}).tex_lines || []).length
        ? "; main.tex lines " + esc(rel.author_source_anchor.tex_lines.join("–"))
        : "") + "</p>" +
      beforeAfter(rel) +
      "<h4>Direct residual</h4>" + residualBlock(rel) +
      "<h4>Direct result</h4><p>" + badge(rel.direct.verdict) + "</p>" +
      why +
      "<h4>Condition / authority</h4><p>" + esc(rel.condition.kind) + ". " + asInline(rel.condition.authority) + "</p>" +
      (rel.condition.tex ? "<div class='block paper math-scroll'>" + asDisplay(rel.condition.tex) + "</div>" : "<p>" + asInline(rel.condition.text) + "</p>") +
      condResidual +
      substitutionDiagram(rel) +
      ruleBox(rel) +
      remainderBox(rel) +
      "<h4>Final status</h4><p>" + badge(rel.final_status) + "</p>" +
      "<h4>Interpretation</h4><p>" + asInline(rel.interpretation) + "</p>" +
      "<p>" + asInline(rel.human_explanation) + "</p>" +
      techDrawer(rel) +
      "</div></details>"
    );
  }

  function leftoverRelations(data, sectionId) {
    const used = {};
    data.chains.forEach(function (c) {
      if (c.section !== sectionId) return;
      c.steps.forEach(function (s) { used[s.relation_id] = true; });
    });
    return data.relations.filter(function (r) {
      return r.section === sectionId && !used[r.id];
    });
  }

  function renderMap(data) {
    return data.sections.map(function (sec) {
      const chains = data.chains.filter(function (c) { return c.section === sec.id; });
      const rest = leftoverRelations(data, sec.id);
      const chainHtml = chains.map(renderChain).join("");
      const restHtml = rest.length
        ? "<h4>Other source-grounded relations in this part</h4>" +
          '<div class="rel-list">' +
          rest.map(function (r) {
            return (
              '<button type="button" class="rel-row" data-open="rel-' + esc(r.id) + '" ' +
              'data-status="' + esc(r.final_status) + '" data-section="' + esc(r.section) + '">' +
              '<span class="eq">' + esc(r.public_display) + "</span>" +
              '<span class="cue">' + asInline(r.math_summary_tex) + "</span>" +
              badge(r.final_status) +
              "</button>"
            );
          }).join("") +
          "</div>"
        : "";
      return (
        '<section class="section-block" id="sec-' + esc(sec.id) + '" data-section="' + esc(sec.id) + '">' +
        "<h3>" + esc(sec.title) + "</h3>" +
        '<p class="lead">' + asInline(sec.summary) + "</p>" +
        chainHtml + restHtml +
        "</section>"
      );
    }).join("");
  }

  function renderAllEdges(data) {
    return data.relations.map(renderEdge).join("");
  }

  function openRel(id) {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.tagName === "DETAILS") el.open = true;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    const btn = el.querySelector("summary") || el;
    if (btn && btn.focus) btn.focus();
    typeset(el);
  }

  function applyFilters() {
    const q = (document.getElementById("q") || {}).value || "";
    const query = q.trim().toLowerCase();
    const status = (document.getElementById("statusFilter") || {}).value || "ALL";
    const section = (document.getElementById("sectionFilter") || {}).value || "ALL";
    document.querySelectorAll("details.edge").forEach(function (el) {
      const okStatus = status === "ALL" || el.getAttribute("data-status") === status ||
        (status === "UNKNOWN_GROUP" && (el.getAttribute("data-status") === "UNKNOWN" || el.getAttribute("data-status") === "UNKNOWN_REMAINDER"));
      const okSec = section === "ALL" || el.getAttribute("data-section") === section;
      const okQ = !query || (el.getAttribute("data-hay") || "").indexOf(query) !== -1;
      el.classList.toggle("hidden", !(okStatus && okSec && okQ));
    });
    document.querySelectorAll(".rel-row").forEach(function (el) {
      const okStatus = status === "ALL" || el.getAttribute("data-status") === status ||
        (status === "UNKNOWN_GROUP" && (el.getAttribute("data-status") === "UNKNOWN" || el.getAttribute("data-status") === "UNKNOWN_REMAINDER"));
      const okSec = section === "ALL" || el.getAttribute("data-section") === section;
      const text = (el.textContent || "").toLowerCase();
      const okQ = !query || text.indexOf(query) !== -1;
      el.classList.toggle("hidden", !(okStatus && okSec && okQ));
    });
    document.querySelectorAll(".section-block").forEach(function (sec) {
      if (section !== "ALL" && sec.getAttribute("data-section") !== section) {
        sec.classList.add("hidden");
      } else {
        sec.classList.remove("hidden");
      }
    });
  }

  function wire(data) {
    document.addEventListener("click", function (ev) {
      const open = ev.target.closest("[data-open]");
      if (open) {
        ev.preventDefault();
        const id = open.getAttribute("data-open");
        history.replaceState(null, "", "#" + id);
        openRel(id);
        return;
      }
      const tog = ev.target.closest("[data-toggle-residual]");
      if (tog) {
        const id = "full-res-" + tog.getAttribute("data-toggle-residual");
        const box = document.getElementById(id);
        if (box) {
          const hide = !box.hasAttribute("hidden");
          if (hide) box.setAttribute("hidden", "");
          else box.removeAttribute("hidden");
          tog.textContent = hide ? "Show full residual" : "Hide full residual";
          typeset(box);
        }
      }
    });
    document.querySelectorAll(".filter-pills button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".filter-pills button").forEach(function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        const sel = document.getElementById("statusFilter");
        if (sel) sel.value = btn.getAttribute("data-status");
        applyFilters();
      });
    });
    ["q", "statusFilter", "sectionFilter"].forEach(function (id) {
      const el = document.getElementById(id);
      if (el) el.addEventListener("input", applyFilters);
      if (el) el.addEventListener("change", applyFilters);
    });
    window.addEventListener("hashchange", function () {
      const id = location.hash.replace(/^#/, "");
      if (id) openRel(id);
    });
    window.addEventListener("beforeprint", function () {
      document.querySelectorAll("details.edge.featured-print, details.edge[open]").forEach(function (d) {
        d.open = true;
      });
      data.featured_overview.forEach(function (row) {
        const el = document.getElementById("rel-" + row.relation_id);
        if (el) el.open = true;
      });
    });
    if (location.hash) openRel(location.hash.replace(/^#/, ""));
    try {
      const params = new URLSearchParams(location.search);
      const openParam = params.get("open");
      if (openParam) {
        const id = openParam.indexOf("rel-") === 0 ? openParam : "rel-" + openParam;
        openRel(id);
      }
      if (params.get("preview") === "flagship") {
        data.featured_overview.forEach(function (row) {
          openRel("rel-" + row.relation_id);
        });
      }
    } catch (e) { /* ignore */ }
  }

  function main() {
    const data = window.AUDIT_REPORT;
    const table = document.getElementById("featured-table");
    const map = document.getElementById("derivation-map");
    const edges = document.getElementById("edge-list");
    if (!data || !table || !map || !edges) {
      const err = document.getElementById("load-error");
      if (err) err.hidden = false;
      return;
    }
    const err = document.getElementById("load-error");
    if (err) err.hidden = true;

    table.innerHTML = renderFeaturedTable(data);
    map.innerHTML = renderMap(data);
    edges.innerHTML = renderAllEdges(data);
    wire(data);
    typeset(document.body);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();
