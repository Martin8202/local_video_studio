"""shots.yaml + API 範本 + node 對照表 -> workflows/out/<project>_shot_XX.json"""
import argparse, copy, json, random, sys, urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("prompt", "negative", "width", "height", "frames", "seconds", "fps", "seed")


def load_shots(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    defaults = cfg.get("defaults", {})
    shots = [{**defaults, **s} for s in cfg["shots"]]
    for s in shots:
        s["id"] = str(s["id"]).zfill(2)
    return cfg.get("project", "project"), shots


def check_nodes(template, server):
    """比對範本用到的 class_type 與 ComfyUI 已安裝的節點，缺少就結束並列出。"""
    with urllib.request.urlopen(f"{server}/object_info", timeout=30) as r:
        installed = json.load(r)
    missing = sorted({n["class_type"] for n in template.values()} - installed.keys())
    if missing:
        raise SystemExit("ComfyUI 缺少節點: " + ", ".join(missing))


def build(shot, template, nodemap):
    """依對照表把 shot 的值填進範本；回傳新的 workflow dict。"""
    wf = copy.deepcopy(template)
    seconds, fps = shot.get("seconds", 5), shot.get("fps", 24)
    seed = shot.get("seed", -1)
    values = {
        **shot,
        "fps": fps,
        "frames": round(seconds * fps / 8) * 8 + 1,  # LTX 幀數需為 8n+1
        "seed": random.randrange(2**32) if seed == -1 else seed,
    }
    for key, target in nodemap.items():
        if key not in FIELDS:
            raise SystemExit(f"對照表有未知欄位: {key}")
        if key not in values:  # 例如 negative 可省略
            continue
        node = wf.get(target["node"])
        if node is None:
            raise SystemExit(f"範本沒有 node {target['node']}（對照表 {key}）")
        node["inputs"][target["field"]] = values[key]
    return wf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots")
    ap.add_argument("--template", default=ROOT / "workflows/templates/ltx2_5_t2v_api.json")
    ap.add_argument("--map", default=ROOT / "workflows/templates/ltx2_5_t2v_map.json")
    ap.add_argument("--out", default=ROOT / "workflows/out")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--no-check", action="store_true", help="ComfyUI 沒開時略過節點驗證")
    a = ap.parse_args()

    template = json.loads(Path(a.template).read_text(encoding="utf-8"))
    nodemap = json.loads(Path(a.map).read_text(encoding="utf-8"))
    if not a.no_check:
        check_nodes(template, a.server)
    project, shots = load_shots(a.shots)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in shots:
        p = out / f"{project}_shot_{s['id']}.json"
        p.write_text(json.dumps(build(s, template, nodemap), ensure_ascii=False, indent=1), encoding="utf-8")
        print(p)


if __name__ == "__main__":
    sys.exit(main())
