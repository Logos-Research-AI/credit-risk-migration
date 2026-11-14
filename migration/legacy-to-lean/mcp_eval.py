"""Call the local logos-mcp server's `eval_decl` tool from a script, so that large batches of
evaluation cases do not have to pass through an agent's context. Same server, same tool."""
import json, urllib.request

URL = "http://localhost:8000/mcp"
BP = "a490bc52-8080-49b4-a6f3-8d3c4d29754a"

class Mcp:
    def __init__(self):
        self.sid = None; self.n = 0
        self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "diffeval", "version": "0"}})
        self._rpc("notifications/initialized", None, notify=True)

    def _rpc(self, method, params, notify=False):
        self.n += 1
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None: body["params"] = params
        if not notify: body["id"] = self.n
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
              headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
        if self.sid: req.add_header("Mcp-Session-Id", self.sid)
        with urllib.request.urlopen(req, timeout=900) as r:
            self.sid = r.headers.get("Mcp-Session-Id") or self.sid
            raw = r.read().decode()
        if notify or not raw.strip(): return None
        if raw.lstrip().startswith("{"): return json.loads(raw)
        last = None
        for line in raw.splitlines():
            if line.startswith("data:"):
                last = json.loads(line[5:].strip())
        return last

    def eval_decl(self, item_id, inputs, decl=None):
        args = {"blueprint_id": BP, "item_id": item_id, "inputs": inputs}
        if decl: args["decl"] = decl
        res = self._rpc("tools/call", {"name": "eval_decl", "arguments": args})
        if "error" in res: raise RuntimeError(res["error"])
        r = res["result"]
        if r.get("structuredContent"): return r["structuredContent"]
        return json.loads(r["content"][0]["text"])

if __name__ == "__main__":
    m = Mcp()
    print(m.eval_decl("def:credit_raw_clean", ['(α := Float) "12.5"'], decl="Sas.inputBest"))
