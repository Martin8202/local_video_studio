"""自我檢查：假 ComfyUI 伺服器 + 假範本 + ffmpeg 測試片。執行：python tests/test_pipeline.py"""
import json, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_workflow as bw, concat as cc, run_comfy as rc

STATE = {}


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, code=200):
        body = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/object_info":
            self._send({"CLIPTextEncode": {}, "EmptyLTXVLatentVideo": {}})
        elif self.path.startswith("/history/"):
            self._send(STATE["history"])
        elif self.path.startswith("/view"):
            self._send(b"MP4DATA")

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self._send({"prompt_id": "abc"})


def main():
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}"

    # build_workflow：填值、8n+1 幀數、缺節點
    template = {"1": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},
                "2": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": 0, "length": 0}}}
    nodemap = {"prompt": {"node": "1", "field": "text"}, "width": {"node": "2", "field": "width"},
               "frames": {"node": "2", "field": "length"}}
    wf = bw.build({"prompt": "hi", "width": 768, "seconds": 5, "fps": 24}, template, nodemap)
    assert wf["1"]["inputs"]["text"] == "hi" and wf["2"]["inputs"]["width"] == 768
    assert wf["2"]["inputs"]["length"] == 121 and template["1"]["inputs"]["text"] == ""
    bw.check_nodes(template, url)
    template["3"] = {"class_type": "Nope", "inputs": {}}
    try:
        bw.check_nodes(template, url)
        raise AssertionError("應該要因缺節點而失敗")
    except SystemExit as e:
        assert "Nope" in str(e)

    # run_comfy：成功、OOM、逾時
    assert rc.submit({}, url) == "abc"
    ok = {"abc": {"status": {"completed": True, "status_str": "success"},
                  "outputs": {"9": {"images": [{"filename": "a.mp4", "subfolder": "", "type": "output"}]}}}}
    STATE["history"] = ok
    with tempfile.TemporaryDirectory() as d:
        paths = rc.download(rc.poll("abc", url, 5, 0.1), d, url)
        assert paths[0].read_bytes() == b"MP4DATA"
    STATE["history"] = {"abc": {"status": {"completed": False, "status_str": "error",
                                           "messages": [["execution_error", {"exception_message": "CUDA out of memory"}]]}}}
    try:
        rc.poll("abc", url, 5, 0.1)
        raise AssertionError("應該要 OOM")
    except rc.ComfyError as e:
        assert e.code == rc.EXIT_OOM
    STATE["history"] = {}
    try:
        rc.poll("abc", url, 0.3, 0.1)
        raise AssertionError("應該要逾時")
    except rc.ComfyError as e:
        assert e.code == rc.EXIT_TIMEOUT

    # concat：同尺寸 copy、不同尺寸 reencode
    with tempfile.TemporaryDirectory() as d:
        def clip(name, size):
            p = Path(d) / name
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=24:duration=1",
                            "-f", "lavfi", "-i", "sine=duration=1", "-c:v", "libx264", "-c:a", "aac",
                            "-shortest", str(p)], check=True, capture_output=True)
            return p
        a, b, c = clip("a.mp4", "320x240"), clip("b.mp4", "320x240"), clip("c.mp4", "160x120")
        assert cc.concat([a, b], Path(d) / "ab.mp4") == "copy"
        assert cc.concat([a, c], Path(d) / "ac.mp4") == "reencode"
        assert cc.size(Path(d) / "ac.mp4") == "320,240"
    print("ALL OK")


if __name__ == "__main__":
    main()
