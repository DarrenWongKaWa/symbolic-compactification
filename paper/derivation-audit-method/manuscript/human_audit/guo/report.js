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

  function whoCertifies(rel) {
    const cond = rel.condition || {};
    if (cond.who_certifies) return String(cond.who_certifies);
    const k = String(cond.kind || "");
    if (k === "source-grounded substitution") return "SOURCE";
    if (k === "author-declared remainder") return "SOURCE";
    if (k.indexOf("rule") >= 0 || k.indexOf("domain") >= 0) return "DOMAIN";
    if (k === "none" || !k) return "";
    if (k.toLowerCase().indexOf("auditor") >= 0) return "AUDITOR";
    return "UPSTREAM";
  }

  function whoBadge(rel) {
    const w = whoCertifies(rel);
    if (!w) return "";
    return '<span class="who ' + esc(w) + '">' + esc(w) + "</span>";
  }

  function typeset(root) {
    if (window.MathJax && window.MathJax.typesetPromise) {
      return window.MathJax.typesetPromise(root ? [root] : undefined).catch(function (err) {
        console.warn("MathJax typeset failed", err);
      });
    }
    return Promise.resolve();
  }

  function loadData() {
    if (window.AUDIT_REPORT) return window.AUDIT_REPORT;
    const node = document.getElementById("audit-data");
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      return null;
    }
  }

  function residualHero(rel) {
    const d = rel.direct || {};
    if (rel.final_status === "CERTIFIED_BY_RULE" || d.verdict === "N/A") {
      return (
        '<div class="integral-box">' +
        "<p><strong>Parent integral is not posed as a residual.</strong></p>" +
        "<p>Local Leibniz = 0. Torus boundary term = declared, not computed. " +
        "Child ZERO plus a rule is not parent ZERO.</p>" +
        "</div>"
      );
    }
    if (d.verdict === "UNKNOWN" || rel.final_status === "UNKNOWN_REMAINDER") {
      const tex = rel.remainder_display_tex
        ? "<div class='math-scroll'>" + asDisplay(rel.remainder_display_tex) + "</div>"
        : "";
      return (
        '<div class="remainder-callout">' +
        tex +
        "<p>The remainder " + asInline("O(\\Gamma)") +
        " (or the analogous remainder on this row) is not certified. " +
        "This is not a claim that the expansion is false.</p>" +
        "</div>"
      );
    }
    if (rel.final_status === "STRUCTURAL") {
      return "<p>No equality was posed. There is no residual to factor.</p>";
    }
    if (rel.final_status === "UNSUPPORTED") {
      return "<p>The current verifier cannot honestly lower this claimed relation. Not a refutation.</p>";
    }
    let html = '<div class="hero nonzero"><div class="k">Direct residual (compiled obligation)</div>';
    if (d.verdict === "ZERO") {
      html += asDisplay("R_{\\mathrm{direct}}=0");
    } else if (d.residual_tex) {
      html += "<div class='math-scroll'>" + asDisplay("R_{\\mathrm{direct}}=" + d.residual_tex) + "</div>";
      if (d.verdict === "NONZERO") {
        html += "<p>" + asInline("R_{\\mathrm{direct}}\\neq 0") + "</p>";
      }
      if (d.residual_tex_full && d.residual_tex_full !== d.residual_tex) {
        html +=
          '<p><button type="button" class="linkish" data-toggle-residual="' + esc(rel.id) + '">Show unfactored residual</button></p>' +
          '<div class="full-residual math-scroll" id="full-res-' + esc(rel.id) + '" hidden>' +
          asDisplay(d.residual_tex_full) +
          "</div>";
      }
    } else {
      html += "<p>Direct check " + badge(d.verdict) + "; compact residual TeX is not in the view model.</p>";
    }
    html += "</div>";
    return html;
  }

  function formsBlock(rel) {
    const left = rel.before && rel.before.tex ? asDisplay(rel.before.tex) : "<p>—</p>";
    const right = rel.after && rel.after.tex ? asDisplay(rel.after.tex) : "<p>—</p>";
    const from = (rel.public_from || []).join(", ") || "left";
    const to = (rel.public_to || []).join(", ") || "right";
    return (
      '<div class="forms">' +
      '<div class="form"><div class="k">' + esc(from) + "</div><div class='math-scroll'>" + left + "</div></div>" +
      '<div class="to" aria-hidden="true">→</div>' +
      '<div class="form"><div class="k">' + esc(to) + "</div><div class='math-scroll'>" + right + "</div></div>" +
      "</div>"
    );
  }

  function whyBlock(rel) {
    if (rel.direct && rel.direct.verdict === "NONZERO" && rel.why_direct_nonzero) {
      return (
        "<h4>Why the direct residual is nonzero</h4>" +
        "<p>" + asInline(rel.why_direct_nonzero) + "</p>"
      );
    }
    return "";
  }

  function conditionBlock(rel) {
    const cond = rel.condition || {};
    if (!cond.kind || cond.kind === "none") {
      return "<h4>Condition " + asInline("A") + "</h4><p>No extra condition is recorded on this row.</p>";
    }
    const tex = cond.tex ? "<div class='math-scroll'>" + asDisplay(cond.tex) + "</div>" : "<p>" + asInline(cond.text) + "</p>";
    return (
      "<h4>Condition " + asInline("A") + " and provenance</h4>" +
      '<div class="cond-row">' +
      "<div>" + tex + "<p>" + esc(cond.authority || "") + "</p></div>" +
      "<div>" + whoBadge(rel) + "</div>" +
      "</div>"
    );
  }

  function condResidual(rel) {
    if (rel.final_status !== "ZERO_UNDER_SUBSTITUTION") return "";
    return (
      "<h4>After the recorded condition</h4>" +
      asDisplay("R_{\\mathrm{cond}}=0") +
      "<p>Machine status " + badge(rel.final_status) +
      ". Direct NONZERO before the substitution is not by itself a paper error.</p>"
    );
  }

  function oneLine(rel) {
    const t = rel.human_explanation || rel.interpretation || "";
    if (!t) return "";
    return '<p class="one-line">' + asInline(t) + "</p>";
  }

  function techDrawer(rel) {
    const t = rel.technical_provenance || {};
    const dump = {
      internal_id: t.internal_id,
      claimed: t.claimed,
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
      '<details class="tech"><summary>Technical provenance (not the mathematics)</summary>' +
      "<p>Internal identifiers are not public equation numbers. " +
      "These strings are frozen encodings, not a second verdict.</p>" +
      "<pre>" + esc(JSON.stringify(dump, null, 2)) + "</pre></details>"
    );
  }

  function haystack(rel) {
    return [
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
      whoCertifies(rel),
      ((rel.author_source_anchor || {}).prose_paraphrase) || "",
      (rel.direct && rel.direct.residual_tex) || "",
    ].join(" ").toLowerCase();
  }

  function renderEdge(rel, opts) {
    opts = opts || {};
    const open = opts.open ? " open" : "";
    return (
      '<details class="edge residual-card ' + esc(rel.final_status) + '" id="rel-' + esc(rel.id) + '"' + open +
      ' data-status="' + esc(rel.final_status) + '" data-section="' + esc(rel.section) +
      '" data-executable="' + (rel.executable ? "1" : "0") +
      '" data-hay="' + esc(haystack(rel)) + '">' +
      "<summary><span><span class='sum-eq'>" + esc(rel.public_display) + "</span>" +
      "<span class='sum-move'>" + esc(rel.author_move) + "</span></span>" +
      badge(rel.final_status) + "</summary>" +
      '<div class="panel">' +
      formsBlock(rel) +
      residualHero(rel) +
      whyBlock(rel) +
      conditionBlock(rel) +
      condResidual(rel) +
      "<h4>Machine status</h4><p>" + badge(rel.final_status) + "</p>" +
      oneLine(rel) +
      techDrawer(rel) +
      "</div></details>"
    );
  }

  function renderAllEdges(data) {
    const flag = "R007";
    const rest = data.relations.filter(function (r) { return r.id !== flag; });
    const exec = rest.filter(function (r) { return r.executable; });
    const other = rest.filter(function (r) { return !r.executable; });
    return (
      "<h3>Other executable obligations</h3>" +
      exec.map(function (r) { return renderEdge(r); }).join("") +
      "<h3>Non-executable rows (no compiled residual)</h3>" +
      other.map(function (r) { return renderEdge(r); }).join("")
    );
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
    document.querySelectorAll("details.edge, table.ledger tbody tr").forEach(function (el) {
      const st = el.getAttribute("data-status") || "";
      const okStatus = status === "ALL" || st === status ||
        (status === "UNKNOWN_GROUP" && (st === "UNKNOWN" || st === "UNKNOWN_REMAINDER"));
      const okSec = section === "ALL" || el.getAttribute("data-section") === section;
      const hay = (el.getAttribute("data-hay") || el.textContent || "").toLowerCase();
      const okQ = !query || hay.indexOf(query) !== -1;
      el.classList.toggle("hidden", !(okStatus && okSec && okQ));
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
          tog.textContent = hide ? "Show unfactored residual" : "Hide unfactored residual";
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
    if (location.hash) openRel(location.hash.replace(/^#/, ""));
    try {
      const params = new URLSearchParams(location.search);
      const openParam = params.get("open");
      if (openParam) {
        const id = openParam.indexOf("rel-") === 0 ? openParam : "rel-" + openParam;
        openRel(id);
      }
    } catch (e) { /* ignore */ }
  }

  function main() {
    const data = loadData();
    const edges = document.getElementById("edge-list");
    const err = document.getElementById("load-error");
    if (err) err.hidden = true;
    if (data && edges && !edges.getAttribute("data-static")) {
      edges.innerHTML = renderAllEdges(data);
    }
    if (data) wire(data);
    typeset(document.body);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();
