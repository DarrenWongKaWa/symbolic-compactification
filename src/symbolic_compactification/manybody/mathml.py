"""Render formulas as MathML for the reviewer pages (no script, no network).

Reviewer HTML is offline and runs under a CSP that forbids scripts, so
MathJax cannot be used; browsers render MathML natively. Two renderers:

- ``latex_to_mathml``: the author's LaTeX as typeset, for the subset the
  cards understand (fractions, roots, sub/superscripts, Greek, operators,
  document macros). An unknown command is shown literally in red, never
  dropped.
- ``expression_to_mathml``: the expression the tool actually checked
  (a SymPy string), with polygamma(k, z) shown as psi^(k)(z).

Both return a complete ``<math>`` element, or None when rendering fails;
callers then show the source text instead.
"""
from __future__ import annotations

import html
import re

from .latex import expand_macros, normalize_exponential, rewrite_over

_GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ϵ", "varepsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ", "varrho": "ϱ",
    "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "ϕ", "varphi": "φ", "chi": "χ",
    "psi": "ψ", "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ",
    "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "ell": "ℓ", "hbar": "ℏ", "partial": "∂", "infty": "∞", "nabla": "∇",
}
_OPERATORS = {
    "pm": "±", "mp": "∓", "cdot": "⋅", "times": "×", "to": "→", "rightarrow": "→",
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "approx": "≈", "simeq": "≃",
    "equiv": "≡", "sim": "∼", "propto": "∝", "in": "∈", "langle": "⟨", "rangle": "⟩",
    "dagger": "†", "prime": "′", "ldots": "…", "cdots": "⋯", "lbrace": "{", "rbrace": "}",
}
_LARGE = {"int": "∫", "sum": "∑", "prod": "∏", "oint": "∮", "iint": "∬"}
_FUNCTIONS = ("exp", "log", "ln", "sin", "cos", "tan", "sinh", "cosh", "tanh", "Re", "Im",
              "lim", "max", "min", "det", "tr", "Tr", "arg")
_SPACING = {",": "0.17em", ";": "0.28em", ":": "0.22em", "!": "-0.17em", " ": "0.25em",
            "quad": "1em", "qquad": "2em"}
_DROP = ("left", "right", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr",
         "biggl", "biggr", "displaystyle", "textstyle", "nonumber", "notag")
_TOKEN = re.compile(r"\\([A-Za-z]+|.)|(\d+(?:\.\d+)?)|([A-Za-z])|(\s+)|(.)", re.S)


def _e(text: str) -> str:
    return html.escape(text, quote=False)


class _Parser:
    def __init__(self, text: str):
        self.tokens = [m for m in _TOKEN.finditer(text)]
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def skip_space(self):
        while self.peek() is not None and self.peek().group(4):
            self.i += 1

    def group(self) -> str:
        """One argument: a braced group or a single atom."""
        self.skip_space()
        tok = self.peek()
        if tok is not None and tok.group(5) == "{":
            self.next()
            return self.sequence(stop="}")
        return self.atom() or "<mrow/>"

    def sequence(self, stop: str | None = None) -> str:
        items: list[str] = []
        while True:
            tok = self.peek()
            if tok is None:
                break
            if stop and tok.group(5) == stop:
                self.next()
                break
            if tok.group(5) in ("^", "_"):
                base = items.pop() if items else "<mrow/>"
                items.append(self.scripts(base))
                continue
            atom = self.atom()
            if atom:
                items.append(atom)
        return "<mrow>" + "".join(items) + "</mrow>"

    def scripts(self, base: str) -> str:
        sub = sup = None
        for _ in range(2):
            self.skip_space()
            tok = self.peek()
            if tok is None or tok.group(5) not in ("^", "_"):
                break
            self.next()
            if tok.group(5) == "^":
                sup = self.group()
            else:
                sub = self.group()
        large = "movablelimits" in base or "largeop" in base
        if sub and sup:
            return f"<{'munderover' if large else 'msubsup'}>{base}{sub}{sup}</{'munderover' if large else 'msubsup'}>"
        if sub:
            return f"<msub>{base}{sub}</msub>"
        return f"<msup>{base}{sup}</msup>"

    def atom(self) -> str:
        tok = self.next()
        if tok is None:
            return ""
        command, number, letter, space, other = tok.groups()
        if space:
            return ""
        if number:
            return f"<mn>{number}</mn>"
        if letter:
            return f"<mi>{letter}</mi>"
        if other:
            if other == "{":
                return self.sequence(stop="}")
            if other == "}":
                return ""
            if other in "&~":
                return '<mspace width="0.25em"/>'
            if other == "'":
                return "<mo>′</mo>"
            if other == "-":
                return "<mo>−</mo>"
            return f"<mo>{_e(other)}</mo>"
        return self.command(command)

    def command(self, name: str) -> str:
        if name in ("frac", "dfrac", "tfrac"):
            num, den = self.group(), self.group()
            return f"<mfrac>{num}{den}</mfrac>"
        if name == "sqrt":
            return f"<msqrt>{self.group()}</msqrt>"
        if name in ("mathrm", "text", "operatorname", "rm"):
            inner = self._raw_group()
            return f'<mi mathvariant="normal">{_e(inner)}</mi>' if len(inner) <= 1 else f"<mi>{_e(inner)}</mi>"
        if name in ("mathcal", "mathscr"):
            return f'<mi mathvariant="script">{_e(self._raw_group())}</mi>'
        if name in ("mathbf", "boldsymbol", "bm"):
            return f'<mrow mathvariant="bold">{self.group()}</mrow>'
        if name in ("hat", "tilde", "bar", "vec", "dot"):
            accent = {"hat": "^", "tilde": "~", "bar": "¯", "vec": "→", "dot": "˙"}[name]
            return f'<mover accent="true">{self.group()}<mo>{accent}</mo></mover>'
        if name in _DROP:
            return ""
        if name in _SPACING:
            return f'<mspace width="{_SPACING[name]}"/>'
        if name in _GREEK:
            return f"<mi>{_GREEK[name]}</mi>"
        if name in _OPERATORS:
            return f"<mo>{_OPERATORS[name]}</mo>"
        if name in _LARGE:
            return f'<mo largeop="true" movablelimits="false">{_LARGE[name]}</mo>'
        if name in _FUNCTIONS:
            return f"<mi>{name}</mi><mo>&#x2061;</mo>"
        if name in ("{", "}", "|", "(", ")", "[", "]"):
            return f"<mo>{_e(name)}</mo>"
        if name == "\\":
            return '<mspace linebreak="newline"/>'
        return f'<mtext mathcolor="#b3261e">\\{_e(name)}</mtext>'   # unknown: visible, never dropped

    def _raw_group(self) -> str:
        self.skip_space()
        tok = self.next()
        if tok is None:
            return ""
        if tok.group(5) != "{":
            return tok.group(0)
        depth, out = 1, []
        while (tok := self.next()) is not None:
            if tok.group(5) == "{":
                depth += 1
            elif tok.group(5) == "}":
                depth -= 1
                if depth == 0:
                    break
            out.append(tok.group(0))
        return "".join(out).strip()


def latex_to_mathml(tex: str, macros: dict | None = None, *, display: bool = True) -> str | None:
    try:
        text = expand_macros(re.sub(r"\\label\{[^}]*\}", "", tex), macros or {})
        text = rewrite_over(normalize_exponential(text))
        body = _Parser(text).sequence()
    except (RecursionError, ValueError, IndexError):
        return None
    mode = "block" if display else "inline"
    return (f'<math xmlns="http://www.w3.org/1998/Math/MathML" display="{mode}">'
            f"{body}</math>")


def expression_to_mathml(text: str, *, display: bool = True) -> str | None:
    """MathML for a SymPy expression string (the tool's own reading)."""
    import sympy
    from sympy.printing.mathml import MathMLPresentationPrinter

    class _Printer(MathMLPresentationPrinter):
        def _print_polygamma(self, expr):          # psi^(k)(z) instead of 'polygamma'
            k, z = expr.args
            mrow = self.dom.createElement("mrow")
            head = self.dom.createElement("msup")
            psi = self.dom.createElement("mi")
            psi.appendChild(self.dom.createTextNode("ψ"))
            head.appendChild(psi)
            order = self.dom.createElement("mrow")
            for part in ("(", None, ")"):
                if part is None:
                    order.appendChild(self._print(k))
                else:
                    mo = self.dom.createElement("mo")
                    mo.appendChild(self.dom.createTextNode(part))
                    order.appendChild(mo)
            head.appendChild(order)
            mrow.appendChild(head)
            fenced = self.dom.createElement("mrow")
            for part in ("(", None, ")"):
                if part is None:
                    fenced.appendChild(self._print(z))
                else:
                    mo = self.dom.createElement("mo")
                    mo.appendChild(self.dom.createTextNode(part))
                    fenced.appendChild(mo)
            mrow.appendChild(fenced)
            return mrow

    known = {"polygamma", "I", "pi", "E", "exp", "log", "cosh", "sinh", "tanh", "cos", "sin",
             "tan", "sqrt", "conjugate", "re", "im", "Abs", "oo", "Rational", "Integer", "Float"}
    local = {}
    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)(\s*\()?", text):
        name, call = m.group(1), m.group(2)
        if name in known or name in local:
            continue
        psi = re.fullmatch(r"psi(\d?)", name)
        if psi and call:
            k = int(psi.group(1) or 0)
            local[name] = (lambda z, k=k: sympy.polygamma(k, z))
        else:
            local[name] = sympy.Function(name) if call else sympy.Symbol(name)
    local.update({"nF": sympy.Function("n_F"), "nB": sympy.Function("n_B")})
    try:
        expr = sympy.sympify(text, locals=local)
        body = _Printer().doprint(expr)
    except Exception:          # display only: any failure falls back to the text
        return None
    body = body.replace("<mo>-</mo>", "<mo>−</mo>")
    mode = "block" if display else "inline"
    return f'<math xmlns="http://www.w3.org/1998/Math/MathML" display="{mode}">{body}</math>'
