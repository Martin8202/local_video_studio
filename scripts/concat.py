"""用 ffmpeg 合併多段 mp4；解析度一致用 -c copy，否則縮放到第一段大小並重新編碼（H.264 veryfast）。"""
import argparse, subprocess, tempfile
from pathlib import Path


def size(path):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()


def concat(inputs, output):
    """回傳 'copy' 或 'reencode'。每段都必須有音軌（LTX-2 輸出本來就有）。"""
    inputs = [Path(p).resolve() for p in inputs]
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    sizes = [size(p) for p in inputs]
    if len(set(sizes)) == 1:
        with tempfile.TemporaryDirectory() as d:
            lst = Path(d) / "list.txt"
            lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in inputs), encoding="utf-8")
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(output)]
            subprocess.run(cmd, check=True, capture_output=True)
        return "copy"
    w, h = sizes[0].split(",")
    n = len(inputs)
    scale = "".join(f"[{i}:v]scale={w}:{h},setsar=1[v{i}];" for i in range(n))
    join = "".join(f"[v{i}][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    cmd = ["ffmpeg", "-y", *[x for p in inputs for x in ("-i", str(p))],
           "-filter_complex", scale + join, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", str(output)]
    subprocess.run(cmd, check=True, capture_output=True)
    return "reencode"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ap.add_argument("inputs", nargs="+")
    a = ap.parse_args()
    print(concat(a.inputs, a.output))
