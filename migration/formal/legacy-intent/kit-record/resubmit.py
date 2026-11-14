"""Re-submit the stored statement draft of every item whose acceptance was cleared by an edit
upstream (the server clears dependents). Nothing is rewritten: each draft is read back from the
server (read_scratch) and submitted unchanged (write_statement), dependencies first.
Optional patches: migration/resubmit.py 'item::old::new' ..."""
import json, sys
sys.path.insert(0, "migration")
from mcp_eval import Mcp, BP

def call(m, name, **args):
    args["blueprint_id"] = BP
    res = m._rpc("tools/call", {"name": name, "arguments": args})
    r = res["result"]
    out = r.get("structuredContent") or json.loads(r["content"][0]["text"])
    return out.get("result", out)

def main():
    patches = {}
    for a in sys.argv[1:]:
        item, old, new = a.split("::"); patches.setdefault(item, []).append((old, new))
    m = Mcp(); failed = {}
    for rnd in range(40):
        st = call(m, "get_status")
        todo = [i for i in st["statements_to_write"] if failed.get(i, 0) < 3]
        if not todo: break
        for item in todo:
            sc = call(m, "read_scratch", item_id=item, part="statement")
            text = sc.get("content") or sc.get("text") or sc.get("draft")
            if text is None: print(item, "NO DRAFT", str(sc)[:200]); failed[item] = 3; continue
            for old, new in patches.get(item, []):
                if old in text: text = text.replace(old, new)
            r = call(m, "write_statement", item_id=item, content=text)
            ok = r.get("success")
            if not ok:
                failed[item] = failed.get(item, 0) + 1
                print(item, "REJECTED", str(r.get("compile_result", r))[:700])
            else: print(item, "accepted")
    st = call(m, "get_status")
    print("formalized", st["statements_formalized"], "of", st["total_items"], "to_write", st["statements_to_write"], "waiting", st["waiting"])

if __name__ == "__main__":
    main()
