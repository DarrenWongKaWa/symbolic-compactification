# AI disclosure plan

Do **not** insert this into `draft-v3`. Draft-v4 and the submission packet
must follow the **PRIMARY** venue’s current policy at submission time.

Access date: 2026-09-02.

This project used AI substantively. That fact is not hidden.
No AI system is an author.

---

## Policies in force (official)

### If PRIMARY = CPC (Elsevier)

Source: https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals
(Elsevier generative AI policies for journals; updated June 2026.)

- Human oversight required. Authors accountable for all content.
- **Manuscript-preparation** AI: declaration section immediately before
  references, titled e.g. “Declaration of generative AI and AI-assisted
  technologies in the manuscript preparation process.”
- Suggested wording: tool name, reason; authors reviewed/edited and take
  full responsibility.
- Basic grammar/spelling/punctuation: no declaration.
- **Research-process** AI (code, analysis, literature synthesis used as
  research): describe in Methods, not only in the writing declaration.
- AI cannot be listed as author.
- Reviewers/editors must not upload confidential manuscripts to AI tools.

### If BACKUP = PRR (APS)

Source: https://journals.aps.org/authors/appropriate-use-ai-tools
(page dated 2026-06-08; APS news 2026-06-17.)

- Substantive AI use **must** be disclosed in the paper: tool name and
  version; how it assisted; how authors directed and verified output.
- Light polish / condense / light edit: **not** required to disclose.
- Research-process AI: Methods.
- Figure-generation AI: figure caption.
- Other disclosable uses: Acknowledgments.
- AI cannot be an author.
- Do not upload unpublished manuscripts or referee reports to unrestricted
  AI tools.

---

## Planned disclosure categories (honest)

### 1. Research use (Methods)

Must be described as tooling, not as verification authority:

- Optional LLM / agent **proposers** in Forward experiments (untrusted;
  cannot self-promote). Frozen verdict:
  `FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS`.
- Agent-assisted **extraction** of source-grounded relations during audit
  campaigns, always checked by the frozen verifier.
- AI-assisted coding of the public implementation, reviewed by the authors.
- Core verification on `v0.3.0-alpha` uses **no** model service and **no**
  API key (L10). That sentence must remain.

Do not write: “AI discovered the next formula”; “AI certified the paper.”

### 2. Manuscript-writing use (declaration / acknowledgments)

Substantive assistance with:

- literature organisation against a frozen search protocol
- structuring Related Work from the frozen primary set
- drafting assistance that authors then rewrite and verify against the
  Claim–Evidence Matrix
- figure layout assistance (TikZ source remains human-editable authority)

Draft-v4 must not treat AI-written sentences as scientific authority.
Every load-bearing number still maps to an L-row.

### 3. Light language polishing

Grammar/clarity edits. Elsevier: no declaration if only spelling/grammar.
APS: no disclosure required for polish/condense/light edit.

If a humanizer is run later, record it here as polishing unless it
rewrites scientific claims (forbidden by the lock).

---

## What will not be disclosed as a scientific result

- Internal chat logs.
- Prompt text, except as needed for reproducibility of optional proposers.
- Unpublished private manuscripts.

---

## CPC-ready declaration stub (not inserted in draft-v3)

```text
Declaration of generative AI and AI-assisted technologies
in the manuscript preparation process

During the preparation of this work the author(s) used [NAME / VERSION]
in order to [literature organisation / drafting assistance / code
assistance as applicable]. After using this tool/service, the author(s)
reviewed and edited the content as needed and take(s) full responsibility
for the content of the published article. Core verification of
mathematical residuals does not use a model service or an API key.
```

Research-process uses go in Methods, not only in this stub.
