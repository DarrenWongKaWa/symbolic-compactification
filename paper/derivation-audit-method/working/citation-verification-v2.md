# Citation verification v2

Ladder: **Rung 1 complete.** Independent sub-agent
`01a05a6e-f0c2-77e3-acb0-4b8172b06b7e` received only the numbered list and
in-text uses, retrieved each entry with at least three query forms, and
graded **all 18 VERIFIED**. No unused refs, no missing refs, numbering 1-18
with no first-appearance gaps. Quote strength: citation-level except Guo
identity (L1 validation report).

Optional metadata from that pass, now applied: [9] pages 625-635;
[10] LNCS 2283; [18] journal *Comput. Phys. Commun.* 308:109457 (2025).

Writer-side Rung 2 notes remain below.

`Butt and Fitch, DKE 2021` from audit-only draft-v2 was dropped from the
manuscript. A matching DKE article exists in `bib/references.bib`
("A provenance model for control-flow driven scientific workflows") but is
unused in draft-v2 prose (Moreau 2008 and Koop 2021 cover that family).

| # | Status | Notes | Quote strength |
|---|---|---|---|
| 1 | VERIFIED | MacCallum, Living Rev. Relativ. 21:6 (2018), doi:10.1007/s41114-018-0015-6 | citation-level CAS in gravity |
| 2 | VERIFIED | Meurer et al., PeerJ Comput. Sci. 3:e103 (2017), doi:10.7717/peerj-cs.103 | citation-level SymPy |
| 3 | VERIFIED | Peeters, Comput. Phys. Commun. 176:550-558 (2007), doi:10.1016/j.cpc.2007.01.003 | citation-level field-theory CAS |
| 4 | VERIFIED | Kluyver et al., ELPUB 2016, pp. 87-90, doi:10.3233/978-1-61499-649-1-87 | citation-level notebooks |
| 5 | VERIFIED | Necula, POPL 1997, pp. 106-119, doi:10.1145/263699.263712 | citation-level PCC |
| 6 | VERIFIED | Gottliebsen, Kelsey, Martin, J. Symbolic Comput. 39(5):539-567 (2005), doi:10.1016/j.jsc.2004.12.005 | citation-level hidden verification |
| 7 | VERIFIED | Kaufmann and Biere, STTT 25(2):133-144 (2023), doi:10.1007/s10009-022-00688-6 | citation-level SAT+CA multiplier verification; **no certificate sizes** |
| 8 | VERIFIED | Moreau, Ludäscher, et al., Concurr. Comput. Pract. Exp. 20(5):409-418 (2008), doi:10.1002/cpe.1233 | citation-level provenance challenge |
| 9 | VERIFIED | de Moura and Ullrich, CADE-28, LNCS 12699, pp. 625-635 (2021), doi:10.1007/978-3-030-79876-5_37 | citation-level Lean 4 |
| 10 | VERIFIED | Nipkow, Paulson, Wenzel, Isabelle/HOL, Springer LNCS 2283, 2002 | citation-level kernel |
| 11 | VERIFIED | Polu and Sutskever, arXiv:2009.03393 (2020) | preprint; citation-level GPT-f |
| 12 | VERIFIED | Trinh et al., Nature 625:476-482 (2024), doi:10.1038/s41586-023-06747-5 | citation-level neuro-symbolic checker |
| 13 | VERIFIED | Yang et al., NeurIPS 2023 | citation-level LeanDojo |
| 14 | VERIFIED | Wilkinson et al., Sci. Data 3:160018 (2016), doi:10.1038/sdata.2016.18 | citation-level FAIR |
| 15 | VERIFIED | Guo et al., Phys. Rev. Lett. 136, 206303 (2026), arXiv:2511.16422v2 | identity of field case; physics not claimed |
| 16 | VERIFIED | Koop, IPAW 2021, LNCS 12839:109-126, doi:10.1007/978-3-030-80960-7_7 | citation-level incomplete notebook provenance |
| 17 | VERIFIED | Song, Yang, Anandkumar, arXiv:2404.12534 (2024) | preprint; citation-level Lean Copilot |
| 18 | VERIFIED | Tooby-Smith, Comput. Phys. Commun. 308:109457 (2025), doi:10.1016/j.cpc.2024.109457; arXiv:2405.08863 | citation-level HepLean |

Physics Derivation Graph: named in Related Work as a software project; no
journal citation fabricated.

Bidirectional: [1]-[18] all cited; no unused numbered entries in the
manuscript list. First-appearance order: [1]-[15] in the Introduction
contribution paragraph; [16] notebooks in Related Work; [17] Lean copilots
in the LM-search paragraph; [18] HepLean immediately after.

Kaufmann STTT prose was rewritten down from "independently checked
certificates" to "used to verify multiplier circuits" / "SAT solving with
Gröbner techniques" to stay at citation level. The independent verifier
confirmed that the STTT paper does emit algebraic certificates, but the
manuscript stays at citation-level SAT+CA multiplier verification and does
not quote certificate sizes.
