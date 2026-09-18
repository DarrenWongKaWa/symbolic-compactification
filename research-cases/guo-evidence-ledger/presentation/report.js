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

  const TIPS = {
    "0": "Machine checked left\u2212right = 0. Local residual only, not a paper pass.",
    "0 if A": "Machine checked 0 after the substitution in column A?. Does not prove A.",
    cite: "Author invoked a named rule. Local identity + declared rule, not a CAS integral.",
    def: "Definition or bookkeeping. No equality to check.",
    sign: "Claimed cancel or vanishing. You must decide if that claim holds.",
    remainder: "Finite terms do not prove the O(\u00b7) or the limit.",
    look: "Not compiled. Special function, named identity, or similar. Do not treat as algebra 0.",
    gap: "Local algebra was not in the frozen table. Not a pass.",
    "\u22600": "Submitted residual is not 0.",
    Sign: "Record that you accept this cancel. Does not change frozen RESULTS.",
    Signed: "Local sign-off. Click again to undo. Parent stays orange."
  };
  const MUST_IDS = ["R050", "R066", "R110", "R132"];

  function signKey(data) {
    const p = (data && data.paper) || {};
    return "ledger-signoffs:" + String(p.arxiv || p.short || "paper");
  }

  function chipSpan(kind, word) {
    const tip = TIPS[word] || "";
    return (
      '<span class="chip ' + esc(kind) + '" title="' + esc(tip) + '" data-tip="' + esc(tip) + '">' +
      esc(word) + "</span>"
    );
  }

  function statusChips(rel) {
    const st = rel.final_status || "";
    const id = rel.id || "";
    const q = queueKind(rel);
    if (q === "must_review") return "";
    if (st === "EXACT_ZERO") return chipSpan("zero", "0");
    if (st === "ZERO_UNDER_SUBSTITUTION") return chipSpan("zero-if-a", "0 if A");
    if (st === "CERTIFIED_BY_RULE") return chipSpan("cite", "cite");
    if (st === "STRUCTURAL" || isDefinition(rel)) return chipSpan("def", "def");
    if (st === "UNKNOWN" || st === "UNKNOWN_REMAINDER") return chipSpan("remainder", "remainder");
    if (st === "NONZERO") return chipSpan("nonzero", "\u22600");
    if (q === "encode_later" || deviationKind(rel) === "encoding_gap") {
      return chipSpan("gap", "gap");
    }
    return chipSpan("look", "look");
  }

  function badge(status) {
    const cls = String(status || "").replace(/[^A-Z_]/g, "") || "UNKNOWN";
    return '<span class="badge ' + cls + '">' + esc(status) + "</span>";
  }

  function loadSigns(data) {
    try {
      const raw = localStorage.getItem(signKey(data || window.AUDIT_REPORT));
      const map = raw ? JSON.parse(raw) : {};
      return map && typeof map === "object" ? map : {};
    } catch (e) {
      return {};
    }
  }

  function saveSigns(data, map) {
    try {
      localStorage.setItem(signKey(data || window.AUDIT_REPORT), JSON.stringify(map));
    } catch (e) { /* ignore quota */ }
  }

  function paintSignButtons(data) {
    const map = loadSigns(data);
    document.querySelectorAll(".sign-btn").forEach(function (btn) {
      const on = !!map[btn.getAttribute("data-sign")];
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.textContent = on ? "Signed" : "Sign";
      const tip = on ? TIPS.Signed : TIPS.Sign;
      btn.setAttribute("title", tip);
      btn.setAttribute("data-tip", tip);
    });
    const n = MUST_IDS.filter(function (id) { return map[id]; }).length;
    const note = document.getElementById("sign-local-note");
    if (note) {
      if (n === 4) {
        note.hidden = false;
        note.classList.remove("hidden");
        note.textContent = "4/4 signed locally. Completeness still not certified.";
      } else {
        note.hidden = true;
        note.classList.add("hidden");
      }
    }
  }

  function toggleSign(btn) {
    const id = btn.getAttribute("data-sign");
    if (!id) return;
    const data = window.AUDIT_REPORT;
    const map = loadSigns(data);
    if (map[id]) delete map[id];
    else map[id] = true;
    saveSigns(data, map);
    paintSignButtons(data);
  }

  function wireTips() {
    let box = document.getElementById("tip-float");
    if (!box) {
      box = document.createElement("div");
      box.id = "tip-float";
      box.setAttribute("role", "tooltip");
      box.hidden = true;
      document.body.appendChild(box);
    }
    function place(el) {
      if (!el.closest(".ledger-wrap")) return;
      const t = el.getAttribute("data-tip");
      if (!t) return;
      box.textContent = t;
      box.hidden = false;
      const r = el.getBoundingClientRect();
      const w = Math.min(22 * 16, window.innerWidth - 16);
      let left = r.left;
      if (left + w > window.innerWidth - 8) left = Math.max(8, window.innerWidth - w - 8);
      let top = r.bottom + 6;
      box.style.maxWidth = w + "px";
      box.style.left = left + "px";
      box.style.top = top + "px";
      const br = box.getBoundingClientRect();
      if (br.bottom > window.innerHeight - 8) {
        box.style.top = Math.max(8, r.top - br.height - 6) + "px";
      }
    }
    function hide() {
      box.hidden = true;
    }
    document.addEventListener("pointerover", function (ev) {
      const el = ev.target.closest("[data-tip]");
      if (el) place(el);
    });
    document.addEventListener("pointerout", function (ev) {
      const el = ev.target.closest("[data-tip]");
      if (!el) return;
      const next = ev.relatedTarget;
      if (next && el.contains(next)) return;
      hide();
    });
    document.addEventListener("focusin", function (ev) {
      const el = ev.target.closest("[data-tip]");
      if (el) place(el);
    });
    document.addEventListener("focusout", hide);
    window.addEventListener("scroll", hide, true);
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
    const st = rel.final_status;
    const d = rel.direct || {};
    if (st === "STRUCTURAL" || st === "UNSUPPORTED") return "";
    if (st === "CERTIFIED_BY_RULE") {
      const rc = rel.rule_certification || {};
      const loc = rc.local_identity
        ? "<div class='math-scroll'>" + asDisplay(rc.local_identity) + "</div>"
        : "";
      return loc;
    }
    if (d.verdict === "UNKNOWN" || st === "UNKNOWN_REMAINDER" || st === "UNKNOWN") {
      return "";
    }
    if (d.verdict === "ZERO") {
      return '<p class="plain-math">R<sub>direct</sub> = 0</p>';
    }
    if (d.residual_tex) {
      return "<div class='math-scroll'>" + asDisplay("R_{\\mathrm{direct}}=" + d.residual_tex) + "</div>";
    }
    return "";
  }

  function formsBlock(rel) {
    const hasL = rel.before && rel.before.tex;
    const hasR = rel.after && rel.after.tex;
    if (!hasL && !hasR) return "";
    if (hasL && (!hasR || rel.before.tex === rel.after.tex)) {
      return "<div class='math-scroll'>" + asDisplay(rel.before.tex) + "</div>";
    }
    const from = (rel.public_from || []).join(", ") || "left";
    const to = (rel.public_to || []).join(", ") || "right";
    return (
      '<div class="forms">' +
      '<div class="form"><div class="k">' + esc(from) + "</div><div class='math-scroll'>" + asDisplay(rel.before.tex) + "</div></div>" +
      '<div class="to" aria-hidden="true">→</div>' +
      '<div class="form"><div class="k">' + esc(to) + "</div><div class='math-scroll'>" + asDisplay(rel.after.tex) + "</div></div>" +
      "</div>"
    );
  }

  function isDefinition(rel) {
    const move = String(rel.author_move || "").trim().toLowerCase();
    return move === "definition" || rel.claimed_type === "DEFINITION_INSERTION";
  }

  function queueKind(rel) {
    const id = rel.id || "";
    if (id === "R050" || id === "R066" || id === "R110" || id === "R132") return "must_review";
    if (id === "R046" || id === "R096" || id === "R093" || id === "R072") return "encode_later";
    const st = rel.final_status;
    if (st === "UNKNOWN_REMAINDER" || st === "UNKNOWN" || st === "UNSUPPORTED") return "out_of_engine";
    return "";
  }

  function deviationKind(rel) {
    const st = rel.final_status;
    if (st !== "UNKNOWN_REMAINDER" && st !== "UNKNOWN" && st !== "UNSUPPORTED") return "";
    if (isDefinition(rel)) return "";
    if (st === "UNKNOWN_REMAINDER" || st === "UNKNOWN") return "needs_judgment";
    const claimed = rel.claimed_type || "";
    if (
      claimed === "ASYMPTOTIC_CLAIM" ||
      claimed === "LIMIT_CLAIM" ||
      claimed === "SPECIAL_FUNCTION_IDENTITY" ||
      claimed === "INTEGRAL_ARGUMENT" ||
      claimed === "GLOBAL_SYMMETRY_PAIRING"
    ) {
      return "needs_judgment";
    }
    const blob = [
      rel.author_move || "",
      rel.math_summary_tex || "",
      ((rel.author_source_anchor || {}).prose_paraphrase) || "",
    ].join(" ").toLowerCase().replace(/\\/g, "");
    const marks = [
      "approximat",
      "vanishes identically",
      "mathcal{m}",
      "feynman",
      "hellmann",
      "equation of motion",
      "convolution",
      "residue",
      "cauchy",
      "geometric contributions cancel",
      "commutator",
      "quantum metric",
      "band-renormalized",
      "purely intraband",
    ];
    for (let i = 0; i < marks.length; i += 1) {
      if (blob.indexOf(marks[i]) !== -1) return "needs_judgment";
    }
    if (claimed === "ALGEBRAIC_EQUIVALENCE" || claimed === "INDEX_RELABELING") {
      return "encoding_gap";
    }
    return "needs_judgment";
  }

  function summaryAsFormula(tex) {
    const t = String(tex || "").trim();
    if (!t) return "";
    if (t.indexOf("$") !== -1) {
      return '<p class="plain-math">' + asInline(t) + "</p>";
    }
    if (/\\[a-zA-Z]/.test(t) || /[_^]/.test(t)) {
      if (/[A-Za-z]{3,}\s+[A-Za-z]{3,}/.test(t)) {
        return '<p class="plain-math">' + asInline(t) + "</p>";
      }
      return "<div class='math-scroll'>" + asDisplay(t) + "</div>";
    }
    return '<p class="plain-math">' + esc(t) + "</p>";
  }

  function gapNote(rel) {
    const id = rel.id || "";
    const st = rel.final_status;
    const q = queueKind(rel);
    const k = deviationKind(rel);
    let lines = null;
    if (id === "R050") {
      lines = [
        "Author claims \\(\\sigma^{(-2)}\\) is purely intraband if \\(T_A+T_{B,\\mathrm{geo}}=0\\).",
        "Machine did not compile this parent. Children may be 0.",
        "You: is that cancel enough?"
      ];
    } else if (id === "R066") {
      lines = [
        "Author claims geometric terms cancel to \\(T_{3B}^{\\mathrm{intra}}\\).",
        "Machine did not compile this parent.",
        "You: did the geometric pieces actually vanish?"
      ];
    } else if (id === "R110" || id === "R132") {
      lines = [
        "Author claims \\(\\mathcal{M}=0\\).",
        "Machine did not compile this parent.",
        "You: is this a real vanishing or a relabel?"
      ];
    } else if (q === "encode_later" || k === "encoding_gap") {
      lines = [
        "Frozen ledger did not accept this row. Local algebra was not compiled. Not Exact."
      ];
    } else if (st === "UNKNOWN_REMAINDER" || st === "UNKNOWN") {
      lines = [
        "Finite 0 does not prove the remainder. Not the Sign queue."
      ];
    }
    if (!lines) return "";
    return (
      '<div class="reviewer-note">' +
      lines.map(function (p) { return "<p>" + p + "</p>"; }).join("") +
      "</div>"
    );
  }

  function cardHead(rel) {
    return (
      '<div class="card-head">' +
      '<p class="card-eq">' + esc(rel.public_display) + "</p>" +
      statusChips(rel) +
      "</div>"
    );
  }

  function formulaBlock(rel) {
    const hasL = rel.before && rel.before.tex;
    const hasR = rel.after && rel.after.tex;
    let html = "";
    if (hasL || hasR) {
      html += formsBlock(rel);
    } else if (rel.remainder_display_tex) {
      html += "<div class='math-scroll'>" + asDisplay(rel.remainder_display_tex) + "</div>";
    } else if (rel.math_summary_tex) {
      html += summaryAsFormula(rel.math_summary_tex);
    }
    const cond = rel.condition || {};
    const condTex = cond.tex;
    const condText = cond.text;
    if (condTex && condTex !== "none") {
      html +=
        '<div class="cond-row"><span class="k">A? / condition</span>' +
        "<div class='math-scroll'>" + asDisplay(condTex) + "</div>" +
        whoBadge(rel) +
        "</div>";
    } else if (condText && condText !== "none") {
      html +=
        '<div class="cond-row"><span class="k">A? / condition</span>' +
        "<div class='math-scroll'>" + asInline(condText) + "</div>" +
        whoBadge(rel) +
        "</div>";
    }
    html += gapNote(rel);
    return html;
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
    if (rel.final_status !== "ZERO_UNDER_SUBSTITUTION") return "";
    const cond = rel.condition || {};
    const tex = cond.tex ? asDisplay(cond.tex) : asInline(cond.text || "");
    return (
      '<div class="cond-row">' +
      "<div class='math-scroll'>" + tex + "</div>" +
      whoBadge(rel) +
      "</div>"
    );
  }

  function condResidual(rel) {
    if (rel.final_status !== "ZERO_UNDER_SUBSTITUTION") return "";
    return '<p class="plain-math">R<sub>cond</sub> = 0</p>';
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
      "</div></details>"
    );
  }

  function clearCards() {
    document.querySelectorAll(
      "#obligation-table tr.card-expand, table.corr tr.card-expand, " +
      "table.must-review tr.card-expand, table.encoding-gap tr.card-expand, .chip-expand"
    ).forEach(function (el) { el.remove(); });
    document.querySelectorAll(
      "#obligation-table tr.selected, table.corr tr.selected, " +
      "table.must-review tr.selected, table.encoding-gap tr.selected, a.eq-node.selected"
    ).forEach(function (el) { el.classList.remove("selected"); });
  }

  function attachCard(data, relId, origin) {
    const raw = String(relId || "").replace(/^#/, "");
    const id = raw.replace(/^rel-/, "").replace(/^row-/, "").replace(/^corr-/, "");
    if (!data || !data.relations) return;
    const rel = data.relations.find(function (r) { return r.id === id; });
    if (!rel) return;
    const body = cardHead(rel) + formulaBlock(rel);
    const node = origin && origin.closest ? origin.closest("a.eq-node") : null;
    if (node) {
      const lane = node.closest(".lane");
      if (!lane) return;
      const existing = lane.querySelector(".chip-expand");
      if (existing && existing.getAttribute("data-rel") === rel.id && node.classList.contains("selected")) {
        clearCards();
        return;
      }
      clearCards();
      node.classList.add("selected");
      const box = document.createElement("div");
      box.className = "chip-expand";
      box.setAttribute("data-rel", rel.id);
      box.innerHTML = body;
      lane.appendChild(box);
      typeset(box);
      box.scrollIntoView({ block: "nearest" });
      return;
    }
    const corrHost = origin && origin.closest
      ? origin.closest("table.corr tbody tr, table.must-review tbody tr, table.encoding-gap tbody tr")
      : null;
    const host = corrHost && !corrHost.classList.contains("card-expand")
      ? corrHost
      : document.getElementById("row-" + id);
    if (!host) return;
    const existing = host.nextElementSibling;
    if (existing && existing.classList.contains("card-expand")) {
      clearCards();
      return;
    }
    clearCards();
    host.classList.add("selected");
    const tr = document.createElement("tr");
    tr.className = "card-expand";
    const td = document.createElement("td");
    td.colSpan = host.children.length || 5;
    td.innerHTML = body;
    tr.appendChild(td);
    host.after(tr);
    typeset(td);
    tr.scrollIntoView({ block: "nearest" });
  }

  function openRel(id) {
    const el = document.getElementById(id);
    if (el) {
      if (el.tagName === "DETAILS") el.open = true;
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      const btn = el.querySelector("summary") || el;
      if (btn && btn.focus) btn.focus();
      typeset(el);
      return;
    }
    if (window.AUDIT_REPORT) attachCard(window.AUDIT_REPORT, id);
  }

  function foldQuery(s) {
    return String(s || "")
      .toLowerCase()
      .replace(/[–—−]/g, "-")
      .replace(/-+/g, "-")
      .trim();
  }

  function compactQuery(s) {
    return foldQuery(s).replace(/[^a-z0-9]+/g, "");
  }

  function matchesQuery(hay, query) {
    if (!query) return true;
    const h = String(hay || "").toLowerCase();
    const q = foldQuery(query);
    if (!q) return true;
    if (h.indexOf(query.toLowerCase()) !== -1) return true;
    if (h.replace(/[–—−]/g, "-").replace(/-+/g, "-").indexOf(q) !== -1) return true;
    if (compactQuery(h).indexOf(compactQuery(q)) !== -1) return true;
    return false;
  }

  function applyFilters() {
    const status = (document.getElementById("statusFilter") || {}).value || "SIGN";
    function ok(el) {
      if (status === "SIGN") return el.getAttribute("data-you") === "sign";
      if (status === "ORANGE") return el.getAttribute("data-hue") === "orange";
      if (status === "EXACT_ZERO") return el.getAttribute("data-status") === "EXACT_ZERO";
      if (status === "ZERO_UNDER_SUBSTITUTION") {
        return el.getAttribute("data-status") === "ZERO_UNDER_SUBSTITUTION";
      }
      if (status === "BLUE") return el.getAttribute("data-hue") === "blue";
      if (status === "RED") return el.getAttribute("data-hue") === "red";
      return true;
    }
    document.querySelectorAll("#obligation-table tbody tr:not(.card-expand)").forEach(function (el) {
      el.classList.toggle("hidden", !ok(el));
    });
    document.querySelectorAll(".stack .seg").forEach(function (s) {
      const f = s.getAttribute("data-filter") || s.getAttribute("data-status");
      s.classList.toggle("active", f === status);
    });
    clearCards();
  }

  function wire(data) {
    document.addEventListener("click", function (ev) {
      const signBtn = ev.target.closest(".sign-btn");
      if (signBtn) {
        ev.preventDefault();
        ev.stopPropagation();
        toggleSign(signBtn);
        return;
      }
      const open = ev.target.closest("[data-open]");
      if (open) {
        ev.preventDefault();
        const id = open.getAttribute("data-open");
        history.replaceState(null, "", "#" + id);
        attachCard(data, id, open);
        return;
      }
      const tr = ev.target.closest(
        "#obligation-table tbody tr, table.corr tbody tr, table.must-review tbody tr, table.encoding-gap tbody tr"
      );
      if (tr && !tr.classList.contains("card-expand")) {
        const fromA = tr.querySelector("[data-open]");
        const fromTr = tr.getAttribute("id") || "";
        attachCard(data, (fromA && fromA.getAttribute("data-open")) || fromTr, tr);
        return;
      }
      const seg = ev.target.closest(".stack .seg");
      if (seg) {
        document.querySelectorAll(".stack .seg").forEach(function (s) {
          s.classList.toggle("active", s === seg);
        });
        const mean = document.getElementById("seg-meaning");
        if (mean) mean.textContent = seg.getAttribute("data-meaning") || "";
        const st = seg.getAttribute("data-filter") || seg.getAttribute("data-status");
        const sel = document.getElementById("statusFilter");
        if (sel && st) {
          sel.value = st === "NONZERO" ? "RED" : st;
          document.querySelectorAll(".filter-pills button").forEach(function (b) {
            b.setAttribute("aria-pressed", b.getAttribute("data-status") === sel.value ? "true" : "false");
          });
          applyFilters();
        }
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
      if (el) el.addEventListener("keyup", applyFilters);
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
    if (data) window.AUDIT_REPORT = data;
    const err = document.getElementById("load-error");
    if (err) err.hidden = true;
    wire(data || {});
    wireTips();
    paintSignButtons(data || {});
    applyFilters();
    typeset(document.body);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();
