"""src/defect-yajang.html(원본) → 저장소 맨 위 (오프라인 홈 화면 앱, GitHub Pages용)

실행: 저장소 폴더에서 python src/build_pwa.py
원본을 고친 뒤 다시 실행하면 index.html · sw.js · version.json 이 갱신된다.
여러 컴퓨터에서 작업하므로 시작 전에 git pull, 끝나면 commit·push.
"""
import datetime
import hashlib
import json
import pathlib
import re
import urllib.request

HERE = pathlib.Path(__file__).parent          # src/
SRC = HERE / "defect-yajang.html"
OUT = HERE.parent                              # 저장소 맨 위 = GitHub Pages가 내보내는 곳
VENDOR = {
    "pdf.min.js": "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js",
    "pdf.worker.min.js": "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js",
    "pdf-lib.min.js": "https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js",
    "xlsx.full.min.js": "https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js",
}

HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#16202b">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="결함 야장">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""


def fetch_vendor():
    vd = OUT / "vendor"
    vd.mkdir(parents=True, exist_ok=True)
    for name, url in VENDOR.items():
        p = vd / name
        if not p.exists():
            print("download", url)
            p.write_bytes(urllib.request.urlopen(url, timeout=60).read())


def make_icons():
    from PIL import Image, ImageDraw, ImageFont

    d = OUT / "icons"
    d.mkdir(parents=True, exist_ok=True)
    for size, name in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")]:
        s = size / 512
        im = Image.new("RGB", (size, size), "#16202b")
        g = ImageDraw.Draw(im)
        # 도면 격자 느낌
        for x in (130, 256, 382):
            g.line([(x * s, 70 * s), (x * s, 442 * s)], fill="#2c3a4a", width=max(1, int(6 * s)))
        # 화살표 + 번호 원 (결함 표시)
        g.line([(150 * s, 380 * s), (285 * s, 245 * s)], fill="#ff5a4e", width=int(26 * s))
        g.polygon([(118 * s, 412 * s), (140 * s, 310 * s), (220 * s, 390 * s)], fill="#ff5a4e")
        g.ellipse([(250 * s, 110 * s), (420 * s, 280 * s)], fill="#ffffff", outline="#ff5a4e", width=int(22 * s))
        try:
            f = ImageFont.truetype("arialbd.ttf", int(120 * s))
        except OSError:
            f = ImageFont.load_default()
        g.text((335 * s, 197 * s), "1", font=f, fill="#d6332a", anchor="mm")
        im.save(d / name)


def build_html(version, built):
    src = SRC.read_text(encoding="utf-8")
    # 외부 글꼴 제거 (오프라인에서 못 받음 → 기기 글꼴 사용)
    src = re.sub(r'<link rel="preconnect"[^>]*>\n', "", src)
    src = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>\n', "", src)
    src = src.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    # CDN → 앱 안의 파일
    src = src.replace(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>',
        f'<script>window.DY_OFFLINE = true; window.DY_WORKER_SRC = "vendor/pdf.worker.min.js"; window.DY_BUILD = "{version}"; window.DY_BUILT = "{built}";</script>\n'
        '<script src="vendor/pdf.min.js"></script>',
    )
    src = src.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js"></script>\n', "")
    src = src.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"></script>', '<script src="vendor/pdf-lib.min.js"></script>')
    src = src.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>', '<script src="vendor/xlsx.full.min.js"></script>')
    assert "cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js\"" not in src, "CDN 스크립트 치환 실패"
    sw = f"""
<script>
if ("serviceWorker" in navigator) {{
  window.addEventListener("load", () => {{
    const hadCtl = !!navigator.serviceWorker.controller;
    let reloaded = false;
    // 새 버전이 적용되면 화면을 한 번 새로 엶 (저장은 기기에 바로바로 되어 있음)
    navigator.serviceWorker.addEventListener("controllerchange", () => {{
      if (!hadCtl || reloaded) return;
      reloaded = true;
      if (typeof flushLocal === "function") flushLocal().finally(() => location.reload()); else location.reload();
    }});
    navigator.serviceWorker.register("sw.js", {{ updateViaCache: "none" }}).then((reg) => {{
      document.addEventListener("visibilitychange", () => {{ if (document.visibilityState === "visible") reg.update().catch(() => {{}}); }});
    }}).catch(() => {{}});
  }});
}}
</script>
<!-- build {version} -->
"""
    return HEAD + src + sw + "</body>\n</html>\n"


def main():
    OUT.mkdir(exist_ok=True)
    fetch_vendor()
    make_icons()
    html_body = SRC.read_bytes()
    version = hashlib.sha256(html_body + (HERE / "build_pwa.py").read_bytes()).hexdigest()[:10]
    built = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    (OUT / "index.html").write_text(build_html(version, built), encoding="utf-8")
    # 앱의 [업데이트 확인] 버튼이 이 파일과 지금 버전을 비교함
    (OUT / "version.json").write_text(json.dumps({"build": version, "built": built}, ensure_ascii=False), encoding="utf-8")
    files = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"] + [f"vendor/{n}" for n in VENDOR]
    (OUT / "sw.js").write_text(
        f"""// 결함 야장 오프라인 캐시 — build_pwa.py가 생성
const CACHE = "dy-{version}";
const FILES = {files!r};
// 새 버전은 기다리지 않고 바로 적용 (아이패드는 앱을 닫아도 옛 버전이 남는 경우가 있음)
self.addEventListener("install", (e) => {{
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", (e) => {{
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener("fetch", (e) => {{
  if (e.request.method !== "GET") return;
  // 앱 화면(index.html): 인터넷이 되면 새로 받고, 4초 안에 안 되면 저장본
  if (e.request.mode === "navigate") {{
    e.respondWith((async () => {{
      const cached = await caches.match("index.html");
      try {{
        const net = await Promise.race([fetch(e.request, {{ cache: "no-store" }}), new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), 4000))]);
        if (net && net.ok) return net;
      }} catch (err) {{}}
      return cached || fetch(e.request);
    }})());
    return;
  }}
  e.respondWith(
    caches.match(e.request, {{ ignoreSearch: true }}).then((hit) => hit || fetch(e.request).catch(() => caches.match("index.html")))
  );
}});
""",
        encoding="utf-8",
    )
    (OUT / "manifest.webmanifest").write_text(
        """{
  "name": "결함 야장",
  "short_name": "결함 야장",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "any",
  "background_color": "#e9edf1",
  "theme_color": "#16202b",
  "icons": [
    { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
""",
        encoding="utf-8",
    )
    (OUT / ".nojekyll").write_text("")
    print("built", version)


if __name__ == "__main__":
    main()
