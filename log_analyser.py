# C:\Development\INN8\getErrorSBSCalls\results\error_report_20260128_142719.txt


#!/usr/bin/env python3
"""
log_analyser.py

Usage:
  python log_analyser.py \results\error_report_20260128_142719.txt
  python log_analyser.py /results/error_report_20260128_142719.txt --json out.json

What it does:
- Parses one or more "Log Entry #..." blocks
- Extracts key fields + root cause
- Prints a structured analysis per entry
- Optionally writes JSON output
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict


@dataclass
class LogAnalysis:
    entry_number: Optional[int]
    log_id: Optional[str]
    created: Optional[str]
    created_by: Optional[str]
    process: Optional[str]
    message_code: Optional[str]
    error_message: Optional[str]
    root_cause: Optional[str]
    root_cause_type: Optional[str]
    failing_component: Optional[str]
    failing_method_hint: Optional[str]
    arguments_hint: Optional[str]
    recommended_next_steps: List[str]
    one_line_summary: Optional[str]


ENTRY_SPLIT_RE = re.compile(r"(?m)^\s*Log Entry\s*#\s*(\d+)\s*$")
LOG_ID_RE = re.compile(r"(?im)^\s*Log ID:\s*(.+?)\s*$")
CREATED_RE = re.compile(r"(?im)^\s*Created:\s*(.+?)\s+by\s+(.+?)\s*$")
PROCESS_RE = re.compile(r"(?im)^\s*Process:\s*(.+?)\s*$")
MESSAGE_CODE_RE = re.compile(r"(?im)^\s*Message Code:\s*(.+?)\s*$")
ERROR_MESSAGE_RE = re.compile(r"(?is)Error Message:\s*(.+?)\n\s*\n")
CALL_EXCEPTION_ARGS_RE = re.compile(
    r"(?is)Could not invoke\s+([a-zA-Z0-9\._$]+)\.execute\s+with arguments\s+(.+?)(?:\n\d+\.\s|\nCaused by:|\Z)"
)

# Root cause patterns:
# 1) Prefer deepest "Caused by: java.lang.IllegalArgumentException: ERROR: ...."
CAUSE_ERROR_RE = re.compile(
    r"(?is)Caused by:\s*(?:java\.lang\.)?([A-Za-z]+Exception)\s*:\s*ERROR:\s*(.+?)\n\s*at\s",
)

# 2) Fallback: any "java.lang.IllegalArgumentException: ERROR: ..."
GENERIC_ERROR_RE = re.compile(
    r"(?is)(?:java\.lang\.)?([A-Za-z]+Exception)\s*:\s*ERROR:\s*(.+?)(?:\n\s*at\s|\Z)"
)

# 3) Identify meaningful app methods near bottom:
FAIL_METHOD_HINT_RE = re.compile(
    r"(?m)^\s*at\s+deployment\.sonata\.ear//(bravura\.[a-zA-Z0-9\._$]+)\((.+?)\)\s*$"
)


def split_entries(text: str) -> List[Dict]:
    """
    Returns list of dicts: {entry_number, raw_text}
    If no 'Log Entry #' markers exist, treat whole file as one entry.
    """
    matches = list(ENTRY_SPLIT_RE.finditer(text))
    if not matches:
        return [{"entry_number": None, "raw_text": text}]

    entries = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entry_number = int(m.group(1))
        raw = text[start:end].strip()
        entries.append({"entry_number": entry_number, "raw_text": raw})
    return entries


def pick_deepest_root_cause(stack: str) -> (Optional[str], Optional[str]):
    """
    Picks the most specific root cause by preferring the LAST match found.
    """
    best_type = None
    best_msg = None

    # Prefer "Caused by:" ERROR
    for m in CAUSE_ERROR_RE.finditer(stack):
        best_type = m.group(1).strip()
        best_msg = m.group(2).strip()

    if best_msg:
        return best_msg, best_type

    # Fallback to any ERROR line
    for m in GENERIC_ERROR_RE.finditer(stack):
        best_type = m.group(1).strip()
        best_msg = m.group(2).strip()

    return best_msg, best_type


def extract_field(regex: re.Pattern, text: str, group: int = 1) -> Optional[str]:
    m = regex.search(text)
    return m.group(group).strip() if m else None


def extract_created(text: str) -> (Optional[str], Optional[str]):
    m = CREATED_RE.search(text)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()


def extract_call_args(text: str) -> (Optional[str], Optional[str]):
    m = CALL_EXCEPTION_ARGS_RE.search(text)
    if not m:
        return None, None
    method = m.group(1).strip()
    args = " ".join(m.group(2).split())
    # Keep it readable: truncate if massive
    if len(args) > 240:
        args = args[:240] + "…"
    return method, args


def extract_failure_hint(stack: str) -> (Optional[str], Optional[str]):
    """
    Grab a meaningful method hint near the bottom (where the error originated).
    We'll take the last match of the application stack pattern.
    """
    last = None
    for m in FAIL_METHOD_HINT_RE.finditer(stack):
        last = m
    if not last:
        return None, None
    return last.group(1).strip(), last.group(2).strip()


def build_recommendations(root_cause: Optional[str], call_method: Optional[str]) -> List[str]:
    rec = []

    if root_cause and "Fee amount unallocated" in root_cause:
        rec.extend([
            "Identify the specific transaction/source record for the failing queue item/transaction ID in the arguments.",
            "Compare the total fee amount vs the sum of allocatable contribution-type amounts for that transaction.",
            "Check for missing/zero/negative contribution types or a mismatch in allocation rules (proportional contribution type allocation).",
            "Confirm whether the transaction is 'unpriced' / partially derived and whether fees are being posted before contribution bases exist.",
            "Correct the underlying allocation data (or fee amount) and re-run/requeue the item."
        ])
    else:
        rec.extend([
            "Locate the failing queue item / transaction using the arguments in the CallException.",
            "Identify the deepest Caused by exception and validate the related business data constraints.",
            "Re-run/requeue after correcting the underlying data condition."
        ])

    if call_method:
        rec.append(f"Review the DAO path for context: {call_method}.execute(...)")

    return rec


def one_line_summary(process: Optional[str], root_cause: Optional[str]) -> Optional[str]:
    if not process and not root_cause:
        return None
    p = process or "Process"
    rc = root_cause or "an application error (see stacktrace)"
    return f"{p} failed due to: {rc}"


def analyse_entry(entry_number: Optional[int], raw: str) -> LogAnalysis:
    log_id = extract_field(LOG_ID_RE, raw)
    created, created_by = extract_created(raw)
    process = extract_field(PROCESS_RE, raw)
    message_code = extract_field(MESSAGE_CODE_RE, raw)
    error_message = extract_field(ERROR_MESSAGE_RE, raw)

    # Root cause is inside stack trace; just use whole raw if needed
    root_msg, root_type = pick_deepest_root_cause(raw)

    call_method, call_args = extract_call_args(raw)
    failing_component, failing_method_hint = extract_failure_hint(raw)

    recs = build_recommendations(root_msg, call_method)

    return LogAnalysis(
        entry_number=entry_number,
        log_id=log_id,
        created=created,
        created_by=created_by,
        process=process,
        message_code=message_code,
        error_message=error_message,
        root_cause=root_msg,
        root_cause_type=root_type,
        failing_component=failing_component,
        failing_method_hint=failing_method_hint,
        arguments_hint=call_args,
        recommended_next_steps=recs,
        one_line_summary=one_line_summary(process, root_msg),
    )


def print_analysis(a: LogAnalysis) -> None:
    header = f"Log Entry #{a.entry_number}" if a.entry_number is not None else "Log Entry"
    print("=" * 90)
    print(header)
    print("-" * 90)

    def line(label: str, value: Optional[str]):
        if value:
            print(f"{label}: {value}")

    line("Log ID", a.log_id)
    if a.created or a.created_by:
        print(f"Created: {a.created or ''} by {a.created_by or ''}".strip())
    line("Process", a.process)
    line("Message Code", a.message_code)
    line("Top-level Error", a.error_message)

    print("\nRoot cause (deepest):")
    if a.root_cause:
        print(f" - {a.root_cause_type or 'Exception'}: {a.root_cause}")
    else:
        print(" - Not found (no recognizable root-cause pattern)")

    if a.failing_component:
        print("\nWhere it fails (app layer hint):")
        print(f" - {a.failing_component} ({a.failing_method_hint or 'unknown location'})")

    if a.arguments_hint:
        print("\nArguments hint (truncated):")
        print(f" - {a.arguments_hint}")

    print("\nInterpretation:")
    if a.root_cause and "Fee amount unallocated" in a.root_cause:
        print(" - Fee allocation could not complete because the total fee exceeds the allocatable base across contribution types.")
        print(" - This is typically a data/business-rule mismatch, not a connectivity/SQL outage.")
    else:
        print(" - The failure appears to be a business-rule or application-layer exception (see root cause).")

    print("\nRecommended next steps:")
    for i, r in enumerate(a.recommended_next_steps, 1):
        print(f" {i}. {r}")

    if a.one_line_summary:
        print("\nOne-line summary:")
        print(f" - {a.one_line_summary}")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse application logs and produce root-cause style analysis.")
    ap.add_argument("logfile", help="Path to the log text file")
    ap.add_argument("--json", dest="json_out", help="Write JSON output to this file path", default=None)
    args = ap.parse_args()

    p = Path(args.logfile)
    if not p.exists():
        raise SystemExit(f"File not found: {p}")

    text = p.read_text(encoding="utf-8", errors="replace")
    entries = split_entries(text)

    analyses: List[LogAnalysis] = []
    for e in entries:
        analyses.append(analyse_entry(e["entry_number"], e["raw_text"]))

    # Print human analysis
    for a in analyses:
        print_analysis(a)

    # Optional JSON
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(
            json.dumps([asdict(a) for a in analyses], indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"Wrote JSON: {out_path}")


if __name__ == "__main__":
    main()
