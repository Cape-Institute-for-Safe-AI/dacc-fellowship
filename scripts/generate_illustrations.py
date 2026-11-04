"""
Generate the site illustrations from assets/illustrations/prompts.yaml.

Each image is generated on white with OpenAI's image API (style references
attached), the white is keyed out to transparency, and the result is saved as
assets/illustrations/<name>.webp. Its width, height and alt text are then
updated in index.html. Requires OPENAI_API_KEY, Pillow and PyYAML.

  python3 scripts/generate_illustrations.py hope          # one image
  python3 scripts/generate_illustrations.py hero hope     # several
  python3 scripts/generate_illustrations.py all           # everything
  python3 scripts/generate_illustrations.py --dry hope    # print prompt only
"""
import base64, concurrent.futures, html, io, json, os, re, sys, urllib.error, urllib.request, uuid
from pathlib import Path

import yaml
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "assets/illustrations/prompts.yaml"
OUT_DIR = ROOT / "assets/illustrations"
INDEX = ROOT / "index.html"
API = "https://api.openai.com/v1/images/edits"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_REFERENCES = 16
REFERENCE_MAX_PX = 1024


def build_prompt(cfg, name):
    return f"{cfg['images'][name]['subject'].strip()}, {cfg['style'].strip()}"


def load_references(cfg, name):
    folder = ROOT / cfg["references"]
    refs = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    refs += [ROOT / p for p in cfg["images"][name].get("references", [])]
    missing = [str(p) for p in refs if not p.is_file()]
    if missing:
        sys.exit(f"{name}: reference file(s) not found: {', '.join(missing)}")
    if not refs:
        sys.exit(f"No reference images in {folder}")
    if len(refs) > MAX_REFERENCES:
        sys.exit(f"{name}: {len(refs)} references; the API accepts at most {MAX_REFERENCES}")
    return refs


def reference_png(path):
    im = Image.open(path)
    im.thumbnail((REFERENCE_MAX_PX, REFERENCE_MAX_PX))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def generate(cfg, name):
    key = os.environ["OPENAI_API_KEY"]
    fields = {"model": cfg["model"], "prompt": build_prompt(cfg, name), "size": cfg["size"],
              "quality": cfg["quality"], "output_format": "png", "n": "1"}
    boundary = uuid.uuid4().hex
    body = b"".join(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                    for k, v in fields.items())
    for ref in load_references(cfg, name):
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="{ref.stem}.png"\r\n'
                 f'Content-Type: image/png\r\n\r\n').encode() + reference_png(ref) + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.load(r)
    return Image.open(io.BytesIO(base64.b64decode(data["data"][0]["b64_json"]))).convert("RGB")


def key_out_white(im):
    # Alpha from the darkest channel: pure white -> transparent, ink -> opaque,
    # with a soft ramp so antialiased line edges don't leave a white halo.
    r, g, b = im.split()
    darkest = ImageChops.darker(ImageChops.darker(r, g), b)
    alpha = darkest.point(lambda v: 0 if v >= 248 else 255 if v <= 212 else int((248 - v) / 36 * 255))
    out = im.copy()
    out.putalpha(alpha)
    return out


def crop_to_subject(im, margin=16):
    l, t, r, b = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    return im.crop((max(0, l - margin), max(0, t - margin), min(im.width, r + margin), min(im.height, b + margin)))


def update_index(name, size, alt):
    src = f'src="assets/illustrations/{name}.webp"'
    page = INDEX.read_text()
    tag = re.search(rf'<img\b[^>]*{re.escape(src)}[^>]*>', page)
    if not tag:
        print(f"  {name}: not referenced in index.html, skipped HTML update")
        return
    new = tag.group(0)
    new = re.sub(r'width="\d+"', f'width="{size[0]}"', new)
    new = re.sub(r'height="\d+"', f'height="{size[1]}"', new)
    new = re.sub(r'alt="[^"]*"', f'alt="{html.escape(alt, quote=True)}"', new)
    INDEX.write_text(page.replace(tag.group(0), new))


def run(cfg, name):
    spec = cfg["images"][name]
    try:
        im = generate(cfg, name)
    except urllib.error.HTTPError as e:
        return f"{name}: HTTP {e.code} {e.read()[:300]!r}"
    if spec.get("resize"):
        im = im.resize(tuple(spec["resize"]), Image.LANCZOS)
    im = key_out_white(im)
    if spec.get("crop"):
        im = crop_to_subject(im)
    im.save(OUT_DIR / f"{name}.webp", quality=86, method=6)
    return name, im.size, spec["alt"].strip()


def main(argv):
    dry = "--dry" in argv
    names = [a for a in argv if a != "--dry"]
    cfg = yaml.safe_load(PROMPTS.read_text())
    if not names or names == ["all"]:
        names = list(cfg["images"])
    unknown = [n for n in names if n not in cfg["images"]]
    if unknown:
        sys.exit(f"Unknown image(s): {', '.join(unknown)}. Choose from: {', '.join(cfg['images'])}")

    if dry:
        for n in names:
            refs = ", ".join(os.path.relpath(p, ROOT) for p in load_references(cfg, n))
            print(f"[{n}]\nreferences: {refs}\n{build_prompt(cfg, n)}\n")
        return

    with concurrent.futures.ThreadPoolExecutor(len(names)) as pool:
        results = list(pool.map(lambda n: run(cfg, n), names))
    for res in results:
        if isinstance(res, str):
            print(res)
            continue
        name, size, alt = res
        update_index(name, size, alt)
        print(f"{name}: saved assets/illustrations/{name}.webp {size[0]}x{size[1]}")


if __name__ == "__main__":
    main(sys.argv[1:])
