#!/usr/bin/env python3
"""Watch a workflow session live, read-only.

Every Claude session keeps a transcript under ~/.claude/projects/. This prints the transcript
of the latest session of a workspace as it grows: what the agent says, every tool call, and
every result. It writes nothing, so no Lean lands in a local file.

usage: migration/watch.py <workspace> [--full] [--once] [--all]
  <workspace>  requirements | legacy | port | prover, or a path to any folder a session ran in
  --full       print results and inputs in full (default: first 400 characters)
  --once       print what there is and exit (default: keep following)
  --all        every session of the workspace, oldest first (default: the latest only)
"""
import json, os, re, sys, time

HERE = os.path.dirname(os.path.realpath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = {a for a in sys.argv[1:] if a.startswith("--")}
if not args:
    sys.exit(__doc__)
ws = args[0]
ws = os.path.realpath(ws if os.path.isdir(ws) else os.path.join(HERE, "workspaces", ws))
proj = os.path.expanduser("~/.claude/projects/" + re.sub(r"[^A-Za-z0-9]", "-", ws))
LIMIT = None if "--full" in flags else 400
TTY = sys.stdout.isatty()
COL = {"say": "1", "call": "36", "result": "2", "think": "35", "user": "33", "head": "1;34"}


def paint(kind, s):
    return f"\033[{COL[kind]}m{s}\033[0m" if TTY else s


def clip(s):
    s = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
    s = s.strip()
    if LIMIT and len(s) > LIMIT:
        s = s[:LIMIT] + f" … [{len(s) - LIMIT} more characters; --full shows all]"
    return s


def text_of(content):
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict):
            out.append(b.get("text") or json.dumps(b, ensure_ascii=False))
        else:
            out.append(str(b))
    return "\n".join(out)


def show(o, tag):
    if o.get("type") not in ("user", "assistant"):
        return
    m = o.get("message") or {}
    t = (o.get("timestamp") or "")[11:19]
    pre = f"{t} {tag}"
    c = m.get("content")
    if isinstance(c, str):
        print(paint("user", f"{pre} PROMPT  ") + clip(c))
        return
    for b in c or []:
        k = b.get("type")
        if k == "text" and b.get("text", "").strip():
            print(paint("say", f"{pre} SAYS    ") + b["text"].strip())
        elif k == "thinking" and (b.get("thinking") or "").strip():
            print(paint("think", f"{pre} THINKS  ") + clip(b["thinking"]))
        elif k == "tool_use":
            name = b.get("name", "").split("__")[-1]
            print(paint("call", f"{pre} CALL    {name}  ") + clip(b.get("input") or {}))
        elif k == "tool_result":
            mark = "ERROR   " if b.get("is_error") else "RESULT  "
            print(paint("result", f"{pre} {mark}" + clip(text_of(b.get("content")))))
    sys.stdout.flush()


def transcripts():
    if not os.path.isdir(proj):
        return []
    main = sorted((f for f in os.listdir(proj) if f.endswith(".jsonl")),
                  key=lambda f: os.path.getmtime(os.path.join(proj, f)))
    if "--all" not in flags:
        main = main[-1:]
    files = []
    for f in main:
        files.append((os.path.join(proj, f), "main"))
        side = os.path.join(proj, f[:-6])  # subagents of that session, if any
        for root, _, names in os.walk(side):
            for n in sorted(names):
                if n.endswith(".jsonl"):
                    files.append((os.path.join(root, n), "sub:" + n[:-6][-6:]))
    return files


pos = {}
announced = set()
if not transcripts():
    print(f"no session has run in {ws} yet; waiting" if "--once" not in flags else f"no session in {ws}")
while True:
    for path, tag in transcripts():
        if path not in announced:
            announced.add(path)
            print(paint("head", f"=== {tag}  {path}"))
        with open(path, "rb") as fh:
            fh.seek(pos.get(path, 0))
            while True:
                line = fh.readline()
                if not line.endswith(b"\n"):
                    break  # incomplete last line: read it next time
                pos[path] = fh.tell()
                try:
                    show(json.loads(line), tag)
                except Exception:
                    pass
    if "--once" in flags:
        break
    time.sleep(1)
