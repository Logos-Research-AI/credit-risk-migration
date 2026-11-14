#!/usr/bin/env python3
"""Isolation hook for a verification workspace (PreToolUse).

Installed as <workspace>/.claude/guard.py next to guard.json. Blocks any tool call that
touches a file of the project outside the workspace, changes the workspace's own .claude
folder, or names a Logos blueprint the workspace must not see. Paths outside the project
are not its concern. Exit 2 blocks the call and shows the reason to the agent.
"""
import json, os, re, sys

def main():
    here = os.path.dirname(os.path.realpath(__file__))
    ws = os.path.dirname(here)
    cfg = json.load(open(os.path.join(here, "guard.json")))
    project = os.path.realpath(os.path.join(ws, cfg["project_root"]))
    read_also = [os.path.realpath(os.path.join(ws, p)) for p in cfg.get("read_also", [])]
    deny_bp = set(cfg.get("deny_blueprints", []))
    ev = json.load(sys.stdin)
    tool = ev.get("tool_name", "")
    ti = ev.get("tool_input") or {}
    cwd = ev.get("cwd") or ws

    def inside(p, root):
        return p == root or p.startswith(root + os.sep)

    def bad(p, write):
        p = os.path.expandvars(os.path.expanduser(p))
        r = os.path.realpath(p if os.path.isabs(p) else os.path.join(cwd, p))
        if not inside(r, project):
            return None
        if inside(r, here):
            return "the workspace's .claude folder is off limits" if write else None
        if inside(r, ws):
            return None
        if not write and any(inside(r, a) for a in read_also):
            return None
        return f"{r} is outside this workspace"

    reasons = []
    if tool in ("Edit", "Write", "NotebookEdit"):
        p = ti.get("file_path") or ti.get("notebook_path")
        if p:
            reasons.append(bad(p, True))
    elif tool == "Read":
        if ti.get("file_path"):
            reasons.append(bad(ti["file_path"], False))
    elif tool in ("Grep", "Glob"):
        if ti.get("path"):
            reasons.append(bad(ti["path"], False))
        for k in ("pattern", "glob") if tool == "Glob" else ("glob",):
            v = ti.get(k) or ""
            if v.startswith(("/", "~")) or ".." in v:
                reasons.append(bad(re.split(r"[*?\[{]", v)[0] or ".", False))
    elif tool == "Bash":
        # every word that could be a path is resolved and checked; .claude counts as a write
        for t in re.split(r"""[\s'"`;|&()<>=,:]+""", ti.get("command") or ""):
            if t == ".." or "/" in t or t.startswith("~") or t.startswith(".claude"):
                reasons.append(bad(re.split(r"[*?\[{]", t)[0] or ".", True if ".claude" in t else False))
    elif tool.startswith("mcp__"):
        vals = [v for v in ti.values() if isinstance(v, str)]
        hit = [v for v in vals if v in deny_bp]
        if hit:
            reasons.append(f"blueprint {hit[0]} is not for this workspace")
    reasons = [r for r in reasons if r]
    if reasons:
        print(f"Blocked by the workspace isolation rule: {reasons[0]}. "
              "This is deliberate; do not work around it.", file=sys.stderr)
        sys.exit(2)

try:
    main()
except SystemExit:
    raise
except Exception as e:  # fail closed
    print(f"Workspace guard failed ({e}); call blocked.", file=sys.stderr)
    sys.exit(2)
