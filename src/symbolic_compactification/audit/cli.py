"""Audit subcommand handlers. E7 fills verify/table/report/package/inventory.

``audit init`` and ``audit inspect`` are implemented against the frozen
workspace loader. Other commands call the layer functions; those layers may
still raise NOT_IMPLEMENTED until their owners land.
"""
from __future__ import annotations

import json

from ..models import ENGINE_VERSION, PACKAGE_VERSION, RELEASE_VERSION
from ..security import redact_public_data, redact_text
from .edges import load_edges
from .evidence import latest_audit_run_id, load_audit_run, verify_audit
from .inventory import inventory_equations, load_equation_manifest
from .package import build_reviewer_package
from .report import generate_audit_report
from .schema import AUDIT_SCHEMA_VERSION, NONZERO, AuditError, table_bucket
from .tables import generate_tables
from .workspace import initialize_audit_workspace, load_audit_workspace


def _print_json(payload: dict) -> None:
    print(json.dumps(
        redact_public_data(payload), sort_keys=True, ensure_ascii=False))


def cmd_audit_init(args) -> int:
    workspace = initialize_audit_workspace(args.directory)
    payload = {
        "status": "AUDIT_INITIALIZED",
        "workspace": str(workspace.root),
        "audit_name": workspace.config.audit_name,
        "schema_version": AUDIT_SCHEMA_VERSION,
        "next_command": (
            f"symbolic-compactification audit inventory {workspace.root}"
        ),
    }
    if args.json:
        _print_json(payload)
        return 0
    print("status:      AUDIT_INITIALIZED")
    print(f"workspace:   {redact_text(str(workspace.root))}")
    print(f"audit_name:  {redact_text(workspace.config.audit_name)}")
    print(f"next:        {redact_text(payload['next_command'])}")
    return 0


def cmd_audit_inventory(args) -> int:
    workspace = load_audit_workspace(args.directory)
    inventory = inventory_equations(workspace, write=True)
    payload = {
        "status": "AUDIT_INVENTORY",
        "workspace": str(workspace.root),
        "equations": len(inventory.equations),
        "duplicate_labels": list(inventory.duplicate_labels),
        "source_hash": inventory.source_hash,
        "warnings": list(inventory.warnings),
    }
    if args.json:
        _print_json(payload)
        return 0
    print("status:      AUDIT_INVENTORY")
    print(f"equations:   {len(inventory.equations)}")
    print(f"duplicates:  {len(inventory.duplicate_labels)}")
    return 0


def _optional_layer(func, workspace, warnings, label):
    try:
        return func(workspace)
    except AuditError as exc:
        if exc.code != "NOT_IMPLEMENTED":
            raise
        warnings.append(f"{label}_not_implemented")
        return None


def cmd_audit_inspect(args) -> int:
    workspace = load_audit_workspace(args.directory)
    warnings: list[str] = []
    inventory = _optional_layer(load_equation_manifest, workspace, warnings, "inventory")
    edges = _optional_layer(load_edges, workspace, warnings, "edges")
    edge_types: dict[str, int] = {}
    lowered = 0
    if edges is not None:
        for edge in edges:
            edge_types[edge.edge_type] = edge_types.get(edge.edge_type, 0) + 1
            if edge.lhs or edge.rhs or edge.residual:
                lowered += 1
    payload = {
        "status": "AUDIT_INSPECT",
        "workspace": str(workspace.root),
        "audit_name": workspace.config.audit_name,
        "schema_version": AUDIT_SCHEMA_VERSION,
        "release_version": RELEASE_VERSION,
        "package_version": PACKAGE_VERSION,
        "engine_version": ENGINE_VERSION,
        "manuscript_source": workspace.config.manuscript_source,
        "manuscript_sha256": workspace.manuscript_sha256,
        "equation_manifest_sha256": workspace.equation_manifest_sha256,
        "edge_manifest_sha256": workspace.edge_manifest_sha256,
        "assumptions_sha256": workspace.assumptions_sha256,
        "verifier_profile": workspace.config.verifier_profile,
        "equations": None if inventory is None else len(inventory.equations),
        "edges": None if edges is None else len(edges),
        "edge_types": edge_types,
        "edges_with_expressions": lowered,
        "integrity_warnings": warnings,
        "note": (
            "inspect counts are workspace inventory, not scientific evidence"
        ),
    }
    if args.json:
        _print_json(payload)
        return 0
    print("status:         AUDIT_INSPECT")
    print(f"workspace:      {redact_text(str(workspace.root))}")
    print(f"audit_name:     {redact_text(workspace.config.audit_name)}")
    print(f"manuscript:     {redact_text(workspace.config.manuscript_source)}")
    print(f"verifier:       {workspace.config.verifier_profile}")
    if inventory is not None:
        print(f"equations:      {len(inventory.equations)}")
    if edges is not None:
        print(f"edges:          {len(edges)}")
        print(f"edge_types:     {json.dumps(edge_types, sort_keys=True)}")
    if warnings:
        print("warnings:       " + ", ".join(warnings))
    print("note:           counts are not scientific evidence")
    return 0


def cmd_audit_verify(args) -> int:
    workspace = load_audit_workspace(args.directory)
    run = verify_audit(workspace)
    status_counts: dict[str, int] = {}
    bucket_counts: dict[str, int] = {}
    for record in run.records:
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
        bucket = table_bucket(record)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    payload = {
        "status": "AUDIT_RUN_RECORDED",
        "workspace": str(workspace.root),
        "run_id": run.run_id,
        "records": len(run.records),
        "run_directory": str(run.directory),
        "status_counts": status_counts,
        "table_counts": bucket_counts,
        "note": (
            "a recorded run is not a claim that the derivation is verified; "
            "read TABLE_VERIFIED.md after `audit table`"
        ),
    }
    if args.json:
        _print_json(payload)
        return 2 if status_counts.get(NONZERO, 0) else 0
    print("status:         AUDIT_RUN_RECORDED")
    print(f"run_id:         {run.run_id}")
    print(f"records:        {len(run.records)}")
    print("status_counts:  " + json.dumps(status_counts, sort_keys=True))
    print("table_counts:   " + json.dumps(bucket_counts, sort_keys=True))
    print("note:           recorded != machine-verified; run audit table")
    return 2 if status_counts.get(NONZERO, 0) else 0


def cmd_audit_table(args) -> int:
    workspace = load_audit_workspace(args.directory)
    run_id = args.run or latest_audit_run_id(workspace)
    run = load_audit_run(workspace, run_id)
    artifacts = generate_tables(workspace, run)
    try:
        from .html import generate_html_report
        generate_html_report(workspace, run)
    except AuditError:
        pass
    payload = {
        "status": "AUDIT_TABLES",
        "run_id": run.run_id,
        "verified": str(artifacts.verified_md),
        "structural": str(artifacts.structural_md),
        "uncertified": str(artifacts.uncertified_md),
        "nonzero": str(artifacts.nonzero_md),
        "json": str(artifacts.table_json),
        "csv": str(artifacts.table_csv),
    }
    if args.json:
        _print_json(payload)
        return 0
    print("status:      AUDIT_TABLES")
    print(f"verified:    {redact_text(str(artifacts.verified_md))}")
    print(f"structural:  {redact_text(str(artifacts.structural_md))}")
    print(f"uncertified: {redact_text(str(artifacts.uncertified_md))}")
    print(f"nonzero:     {redact_text(str(artifacts.nonzero_md))}")
    return 0


def cmd_audit_report(args) -> int:
    workspace = load_audit_workspace(args.directory)
    run_id = args.run or latest_audit_run_id(workspace)
    run = load_audit_run(workspace, run_id)
    path = generate_audit_report(workspace, run)
    html_path = None
    try:
        from .html import generate_html_report
        html_path = generate_html_report(workspace, run)
    except AuditError:
        html_path = None
    payload = {
        "status": "AUDIT_REPORT",
        "path": str(path),
        "html_path": str(html_path) if html_path else None,
        "run_id": run.run_id,
    }
    if args.json:
        _print_json(payload)
        return 0
    print("status:      AUDIT_REPORT")
    print(f"path:        {redact_text(str(path))}")
    if html_path is not None:
        print(f"html:        {redact_text(str(html_path))}")
    return 0


def cmd_audit_package(args) -> int:
    workspace = load_audit_workspace(args.directory)
    run_id = args.run or latest_audit_run_id(workspace)
    run = load_audit_run(workspace, run_id)
    dest = build_reviewer_package(workspace, run, dest=args.dest)
    payload = {
        "status": "AUDIT_PACKAGE",
        "path": str(dest),
        "run_id": run.run_id,
    }
    if args.json:
        _print_json(payload)
        return 0
    print("status:      AUDIT_PACKAGE")
    print(f"path:        {redact_text(str(dest))}")
    return 0


def dispatch_audit(args) -> int:
    command = getattr(args, "audit_command", None)
    handlers = {
        "init": cmd_audit_init,
        "inventory": cmd_audit_inventory,
        "inspect": cmd_audit_inspect,
        "verify": cmd_audit_verify,
        "table": cmd_audit_table,
        "report": cmd_audit_report,
        "package": cmd_audit_package,
    }
    handler = handlers.get(command)
    if handler is None:
        raise AuditError("AUDIT_COMMAND_INVALID", f"unknown audit command {command!r}")
    return handler(args)
