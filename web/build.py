"""휴대폰 브라우저용 단일 HTML 빌드 + 설치형 웹앱(GitHub Pages) + 앱용 engine-data.json 생성.

서버의 데이터(JSON)와 키워드 표를 그대로 넣고, 브라우저 엔진(engine.js)이
Python 엔진과 같은 점수를 내는지 확인한 뒤 dist/index.html 을 만든다.

    python3 web/build.py
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent
SERVER = WEB.parent / "server"
sys.path.insert(0, str(SERVER))

from app import repository  # noqa: E402
from app.engine.scoring import TAG_LABELS, score_pairing  # noqa: E402
from app.services import food_parser  # noqa: E402

# 키워드 추정 경로까지 대조하기 위한 DB 밖 음식들
PARITY_EXTRA_FOODS = ["매운 돼지 숯불구이", "트러플 크림 뇨끼", "소스 듬뿍 전복 버터구이", "연어 데리야끼", "초콜릿 무스"]


def build_data() -> dict:
    return {
        "beverages": [b.model_dump() for b in repository.beverages()],
        "foods": [f.model_dump() for f in repository.foods()],
        "tagLabels": TAG_LABELS,
        "keywords": [[list(w), p, t, a] for w, p, t, a in food_parser.KEYWORDS],
        "keywordBase": food_parser.BASE,
    }


def expected_scores() -> list[dict]:
    foods = list(repository.foods()) + [food_parser.parse_food(n) for n in PARITY_EXTRA_FOODS]
    out = []
    for f in foods:
        for b in repository.beverages():
            score, reasons = score_pairing(b, f)
            out.append({"food": f.model_dump(), "bev": b.id, "score": score,
                        "reasons": [r.model_dump() for r in reasons]})
    return out


PARITY_JS = """
const fs = require('fs');
require(process.argv[2]);
const data = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const cases = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const engine = PairingEngine.createEngine(data);
const bevs = Object.fromEntries(data.beverages.map((b) => [b.id, b]));
let bad = 0;
for (const c of cases) {
  const food = c.food.id.startsWith('custom:') ? engine.parseFood(c.food.name_ko) : c.food;
  const got = engine.scorePairing(bevs[c.bev], food);
  if (JSON.stringify(got) !== JSON.stringify({ score: c.score, reasons: c.reasons })) {
    if (bad++ < 5) console.error('MISMATCH', c.food.name_ko, c.bev, JSON.stringify(got), JSON.stringify(c));
  }
}
console.log(`${cases.length - bad}/${cases.length} 일치`);
process.exit(bad ? 1 : 0);
"""


def check_parity(data: dict, tmp: Path) -> None:
    (tmp / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (tmp / "cases.json").write_text(json.dumps(expected_scores(), ensure_ascii=False), encoding="utf-8")
    (tmp / "parity.js").write_text(PARITY_JS, encoding="utf-8")
    subprocess.run(
        ["node", str(tmp / "parity.js"), str(WEB / "engine.js"), str(tmp / "data.json"), str(tmp / "cases.json")],
        check=True,
    )


def main() -> None:
    data = build_data()
    dist = WEB / "dist"
    dist.mkdir(exist_ok=True)
    tmp = dist / ".parity"
    tmp.mkdir(exist_ok=True)
    check_parity(data, tmp)

    # 모바일 앱(app/)도 같은 데이터·엔진을 쓴다. 생성 파일이므로 직접 고치지 말 것.
    (WEB / "engine-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    html = (WEB / "template.html").read_text(encoding="utf-8")
    html = html.replace("/*__ENGINE__*/", (WEB / "engine.js").read_text(encoding="utf-8"))
    # </script> 가 데이터 안에 들어가도 스크립트가 끊기지 않게 이스케이프
    html = html.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (dist / "index.html").write_text(html, encoding="utf-8")
    print(f"dist/index.html ({len(html.encode()) // 1024}KB)")
    build_site(html, dist / "site")


SITE_HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="음식을 먼저 입력하면 어울리는 와인 품종과 사케를 점수 순으로 보여주는 페어링 앱">
<meta name="theme-color" content="#7A1F3D">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="먹는거 먼저">
<style>
  :root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
  body { margin: 0; }
  [hidden] { display: none !important; }
</style>
</head>
<body>
"""

SITE_TAIL = """
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
  }
</script>
</body>
</html>
"""

MANIFEST = {
    "name": "먹는거 먼저",
    "short_name": "먹는거 먼저",
    "description": "음식을 먼저 입력하면 어울리는 와인 품종과 사케를 점수 순으로 보여줍니다.",
    "lang": "ko",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#FBF8F6",
    "theme_color": "#7A1F3D",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

# 같은 출처 파일은 먼저 캐시에서 보여주고 뒤에서 새로 받아 둔다. 오프라인에서도 열린다.
SERVICE_WORKER = """const CACHE = 'meokneungeo-__VERSION__';
const CORE = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  const cacheable = url.origin === location.origin || url.hostname.endsWith('fonts.googleapis.com') || url.hostname.endsWith('fonts.gstatic.com');
  if (e.request.method !== 'GET' || !cacheable) return;
  e.respondWith(caches.open(CACHE).then(async (cache) => {
    const cached = await cache.match(e.request, { ignoreSearch: true });
    const fresh = fetch(e.request).then((res) => {
      if (res.ok || res.type === 'opaque') cache.put(e.request, res.clone());
      return res;
    }).catch(() => cached);
    return cached || fresh;
  }));
});
"""


def build_site(page: str, site: Path) -> None:
    """GitHub Pages 에 올리는 설치형 웹앱(PWA). 모든 경로는 상대 경로라 하위 폴더 주소에서도 동작한다."""
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(parents=True)
    index = SITE_HEAD + page + SITE_TAIL
    (site / "index.html").write_text(index, encoding="utf-8")
    (site / "manifest.webmanifest").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=1), encoding="utf-8")
    # 페이지나 아이콘 중 하나라도 바뀌면 캐시 버전이 바뀌어 설치된 기기도 새 파일을 받는다.
    digest = hashlib.sha256(index.encode())
    for icon in sorted((WEB / "icons").iterdir()):
        shutil.copy(icon, site / icon.name)
        digest.update(icon.read_bytes())
    version = digest.hexdigest()[:10]
    (site / "sw.js").write_text(SERVICE_WORKER.replace("__VERSION__", version), encoding="utf-8")
    (site / ".nojekyll").write_text("", encoding="utf-8")
    print(f"dist/site/ (PWA, 캐시 버전 {version})")


if __name__ == "__main__":
    main()
