# AUDIT_SCHEMA

`audit.json` is the scientific source of truth. Renderer copies statuses.

```json
{
  "paper": {"id": "", "title": "", "source": "", "authors": ""},
  "summary": {
    "overall_state": "AUDIT_INCOMPLETE",
    "claim_count": 0,
    "relations_reconstructed": 0,
    "machine_certified_edges": 0,
    "assumption_dependent_edges": 0,
    "unresolved_load_bearing": 0
  },
  "inventory": {
    "v2": {"total": 0, "main": 0, "appendix": 0, "by_appendix_letter": {}},
    "equations": [{"id": "M-1", "public": "(1)", "section": "main", "tex_label": null, "cue": ""}]
  },
  "claims": [{
    "id": "C1",
    "statement": "",
    "supporting_equations": [],
    "assumptions": [],
    "status": "GAP",
    "unresolved": []
  }],
  "edges": [{
    "id": "E-1",
    "from_eq": "(1)",
    "to_eq": "(2)",
    "transformation": "substitution",
    "assumptions": [],
    "status": "GAP",
    "locator": "",
    "load_bearing": true,
    "central": true
  }],
  "reviewer_obligations": [{
    "id": "O1",
    "priority": 1,
    "status": "HUMAN_REVIEW",
    "claim_used": "",
    "why_not_certified": "",
    "paper_evidence": "",
    "reviewer_must_decide": "",
    "blocks": ["C1"],
    "actions": ["Accept assumption/reasoning", "Reject", "Needs derivation"]
  }],
  "presentation": {
    "central_path": "",
    "central_edge_ids": [],
    "chip_href": {},
    "claims": {},
    "edge_ops": {},
    "obligation_titles": {},
    "obligation_need": {}
  }
}
```

`presentation` is optional and must not change a scientific status.
Allowed statuses: see STATUSES.md.
