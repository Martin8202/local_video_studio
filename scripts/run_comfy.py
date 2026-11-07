"""送出 workflow、輪詢、下載 mp4。結束碼: 0 成功 / 1 其他錯誤 / 2 OOM / 3 逾時"""
import argparse, json, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

SERVER = "http://127.0.0.1:8188"
EXIT_OK, EXIT_ERR, EXIT_OOM, EXIT_TIMEOUT = 0, 1, 2, 3


class ComfyError(Exception):
    def __init__(self, msg, code=EXIT_ERR):
        super().__init__(msg)
        self.code = code


def _get(server, path):
    with urllib.request.urlopen(server + path, timeout=60) as r:
        return r.read()


def submit(workflow, server=SERVER):
    req = urllib.request.Request(
        server + "/prompt",
        json.dumps({"prompt": workflow}).encode(),
        {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["prompt_id"]
    except urllib.error.HTTPError as e:  # 節點驗證失敗時 ComfyUI 回 400 並附說明
        raise ComfyError(f"submit 失敗 {e.code}: {e.read().decode(errors='replace')}")


def poll(prompt_id, server=SERVER, timeout=1800, interval=5):
    """等到 history 出現該 id；失敗丟 ComfyError（OOM 用 EXIT_OOM）。回傳 history entry。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        entry = json.loads(_get(server, f"/history/{prompt_id}")).get(prompt_id)
        if entry and entry.get("status", {}).get("completed") is not None:
            st = entry["status"]
            if st.get("status_str") == "error":
                text = json.dumps(st.get("messages", []), ensure_ascii=False)
                oom = "out of memory" in text.lower()
                raise ComfyError(text, EXIT_OOM if oom else EXIT_ERR)
            return entry
        time.sleep(interval)
    raise ComfyError(f"等待 {prompt_id} 逾時（{timeout}s）", EXIT_TIMEOUT)


def download(entry, dest, server=SERVER):
    """把 history entry 內所有 .mp4 輸出存到 dest，回傳路徑清單。"""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for node_out in entry.get("outputs", {}).values():
        for items in node_out.values():
            if not isinstance(items, list):
                continue
            for f in items:
                if isinstance(f, dict) and str(f.get("filename", "")).endswith(".mp4"):
                    q = urllib.parse.urlencode(
                        {k: f.get(k, "") for k in ("filename", "subfolder", "type")}
                    )
                    p = dest / f["filename"]
                    p.write_bytes(_get(server, "/view?" + q))
                    saved.append(p)
    if not saved:
        raise ComfyError("history 裡找不到 mp4 輸出")
    return saved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("--dest", default="output")
    ap.add_argument("--server", default=SERVER)
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args()
    try:
        wf = json.loads(Path(a.workflow).read_text(encoding="utf-8"))
        pid = submit(wf, a.server)
        for p in download(poll(pid, a.server, a.timeout), a.dest, a.server):
            print(p)
    except ComfyError as e:
        print(f"ERROR[{e.code}]: {e}", file=sys.stderr)
        return e.code
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
