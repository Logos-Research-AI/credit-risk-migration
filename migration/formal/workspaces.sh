#!/bin/bash
# Builds the isolated workspaces for the verification sessions, under
# migration/formal/workspaces/ (git-ignored). Each holds only what its session may see,
# and a PreToolUse hook (guard.py) blocks every file of the project outside it.
# usage: migration/formal/workspaces.sh [name ...]     names: requirements sas python prover
#        (default: all four; an existing workspace is never overwritten)
# WORKSPACES_DIR overrides the destination (for testing the script only).
set -euo pipefail
F=$(cd "$(dirname "$0")" && pwd)
SRC=$(cd "$F/../.." && pwd)
DST=${WORKSPACES_DIR:-$F/workspaces}
KIT=$(dirname "$SRC")/logos-migration-kit
[ -d "$KIT" ] || { echo "kit not found at $KIT"; exit 1; }
SAS_BP='"sas-credit-risk-spec", "a490bc52-8080-49b4-a6f3-8d3c4d29754a"'
PY_BP='"py-credit-risk-port", "b41b22d4-720d-4290-b593-39ceab961986"'

finish() {  # workspace  read_also  deny_blueprints  brief
  local W=$1
  mkdir -p "$W/.claude"
  cp "$F/guard.py" "$W/.claude/guard.py"
  printf '{\n  "project_root": "../../../..",\n  "read_also": [%s],\n  "deny_blueprints": [%s]\n}\n' "$2" "$3" > "$W/.claude/guard.json"
  cat > "$W/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Edit|Write|NotebookEdit|Grep|Glob|Bash|mcp__.*",
        "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/guard.py\"" }]
      }
    ]
  }
}
JSON
  cp "$F/$4" "$W/PROMPT.md"
  [ -e "$W/.gitignore" ] || printf '.venv/\n__pycache__/\n' > "$W/.gitignore"
  (cd "$W" && git init -q && git add -A &&
   git commit -q -m "Workspace snapshot from sas-migration $(cd "$SRC" && git rev-parse --short HEAD)")
  echo "created $W"
}
foundation() { mkdir -p "$1/foundation"; cp "$F/foundation/foundation.pdf" "$F/foundation/foundation.tex" "$1/foundation/"; }
RULE='Never read a file of the project outside this folder; a hook blocks it, and that is deliberate.'

build_requirements() {
  local W=$DST/requirements; mkdir -p "$W"; foundation "$W"
  cp "$SRC/MODEL_CARD.md" "$SRC/README.md" "$F/requirements/requirements.md" "$W/"
  cat > "$W/CLAUDE.md" <<MD
# This workspace: requirements to Lean

Standing rules for every session and subagent here. They override convenience.

- You formalise \`requirements.md\` into the Logos blueprint \`credit-risk-requirements\` and prove it
  consistent. \`PROMPT.md\` is the brief.
- The documentation is the authority. Never look for the SAS or Python code. $RULE
  Never open a blueprint other than \`credit-risk-requirements\` and \`credit-risk-foundation\`.
- All Lean lives in the blueprint. Never save Lean to a local file.
MD
  finish "$W" "" "$SAS_BP, $PY_BP" requirements/brief.md
}

build_sas() {  # the original code, its documentation, real SAS outputs, raw SAS experiments
  local W=$DST/sas; mkdir -p "$W/judge" "$W/experiments"; foundation "$W"
  cp "$SRC"/*.sas "$SRC/MODEL_CARD.md" "$SRC/README.md" "$W/"
  cp -R "$SRC/data" "$W/data"
  cp "$SRC/judge/README.md" "$SRC/judge/run_sas.py" "$SRC/judge/known_warnings.txt" \
     "$SRC/judge/pyproject.toml" "$SRC/judge/uv.lock" "$W/judge/"
  cp -R "$SRC/judge/reference" "$W/judge/reference"
  cp -R "$SRC/judge/scenarios" "$W/judge/scenarios"
  # raw SAS programs, logs and listings only: the findings notes discuss the Python port
  find "$SRC/migration/experiments" -maxdepth 1 \( -name '*.sas' -o -name '*.log' -o -name '*.lst' \) \
     -exec cp {} "$W/experiments/" \;
  printf 'data/\njudge/reference/\n.venv/\n__pycache__/\nout/\n' > "$W/.gitignore"
  cat > "$W/CLAUDE.md" <<MD
@$KIT/CLAUDE.md

# This workspace: SAS to Lean

Standing rules for every session and subagent here. They override convenience.

- You translate the SAS code in this folder to Lean, in the Logos blueprint \`sas-credit-risk-spec\`.
- A separate team translates a Python port of this code. A third proves the two translations
  equivalent. That proof means something only if the translations are independent. So: never
  look for the Python port anywhere. $RULE
  Never open or search any Logos blueprint other than \`sas-credit-risk-spec\`,
  \`credit-risk-requirements\` and \`credit-risk-foundation\`.
- \`judge/README.md\` mentions the port in places. Use it for what it says about SAS only.
- The shared types are in \`foundation/foundation.pdf\`. Never redefine or work around them.
- All Lean lives in the blueprint. Never save Lean to a local file.
MD
  finish "$W" "" "$PY_BP" legacy-intent/brief-translator.md
}

build_python() {  # the port, its lock file, raw inputs
  local W=$DST/python; mkdir -p "$W/inputs"; foundation "$W"
  cp -R "$SRC/credit_risk" "$W/credit_risk"
  find "$W/credit_risk" -name '__pycache__' -type d -prune -exec rm -rf {} +
  cp "$SRC/pyproject.toml" "$SRC/uv.lock" "$W/"
  cp -R "$SRC/data" "$W/data"
  cp -R "$SRC/judge/scenarios" "$W/inputs/scenarios"
  # the 70/30 split is an input of the port (row ids only)
  python3 - "$SRC/judge/reference/model_features_train.csv" "$W/inputs/split_ids.csv" <<'PY'
import csv, sys
with open(sys.argv[2], "w") as f:
    f.write("row_id\n")
    for r in csv.DictReader(open(sys.argv[1])):
        f.write(r["row_id"] + "\n")
PY
  printf 'data/\n.venv/\n__pycache__/\nout/\n' > "$W/.gitignore"
  cat > "$W/CLAUDE.md" <<MD
@$KIT/CLAUDE.md

# This workspace: Python to Lean

Standing rules for every session and subagent here. They override convenience.

- You translate the Python package \`credit_risk/\` to Lean, in the Logos blueprint
  \`py-credit-risk-port\`.
- The package is a port of a SAS pipeline. A separate team translates the SAS original. A third
  proves the two translations equivalent. That proof means something only if the translations
  are independent. So: never look for the SAS code or its outputs anywhere. $RULE
  Never open or search any Logos blueprint other than \`py-credit-risk-port\` and
  \`credit-risk-foundation\`.
- Comments in the Python say what SAS does. They are claims by the port's authors, not your
  source. Translate what the Python code does.
- The shared types are in \`foundation/foundation.pdf\`. Never redefine or work around them.
- All Lean lives in the blueprint. Never save Lean to a local file.
MD
  finish "$W" "" "$SAS_BP" equivalence/brief-translator.md
}

build_prover() {
  local W=$DST/prover; mkdir -p "$W"
  cp "$F/equivalence/informal-spec.md" "$W/"
  cat > "$W/CLAUDE.md" <<MD
# This workspace: equivalence proofs

Standing rules for every session and subagent here. They override convenience.

- You prove or disprove the contracts of \`informal-spec.md\`, in the Logos blueprint
  \`py-credit-risk-port\`. \`PROMPT.md\` is the brief.
- Never change an existing item in any blueprint. Never reword a contract. Never add a
  hypothesis the plan does not allow. A disproof is a good result; a weakened proof is not.
- You may read the two source folders (\`../sas\`, \`../python\`); write only here and in the
  blueprint. A hook blocks every other file of the project, and that is deliberate.
- All Lean lives in the blueprint. Never save Lean to a local file.
MD
  finish "$W" '"../sas", "../python"' "" equivalence/brief-prover.md
}

[ $# -gt 0 ] || set -- requirements sas python prover
for n in "$@"; do
  [ -e "$DST/$n" ] && { echo "$DST/$n exists; left as it is"; continue; }
  case $n in requirements|sas|python|prover) "build_$n";; *) echo "unknown workspace: $n"; exit 1;; esac
done
