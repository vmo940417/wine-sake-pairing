"""점수 엔진 대조 + engine-data.json 생성, 그리고 '먹는거 먼저' 옛 주소용 이사 안내 페이지 빌드.

서버의 데이터(JSON)와 키워드 표를 그대로 넣고, 브라우저 엔진(engine.js)이
Python 엔진과 같은 점수를 내는지 확인한 뒤 dist/index.html 을 만든다.

    python3 web/build.py
"""
import base64
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


NEW_HOME = "https://vmo940417.github.io/vmo/liquor-app/"


def moved_page() -> str:
    """'먹는거 먼저' → '오늘술상' 이사 안내 페이지 (claude.ai 웹 버전과 GitHub Pages 공통)."""
    html = (WEB / "moved.html").read_text(encoding="utf-8")
    icon = base64.b64encode((WEB / "icons" / "sulsang-192.png").read_bytes()).decode()
    return (html.replace("__ICON__", f"data:image/png;base64,{icon}")
            .replace("__QR__", (WEB / "icons" / "qr-sulsang.svg").read_text(encoding="utf-8"))
            .replace("__URL__", NEW_HOME))


def main() -> None:
    data = build_data()
    dist = WEB / "dist"
    dist.mkdir(exist_ok=True)
    tmp = dist / ".parity"
    tmp.mkdir(exist_ok=True)
    check_parity(data, tmp)

    # 오늘술상(vmo 저장소 liquor-app)과 모바일 앱(app/)이 쓰는 데이터. 생성 파일이므로 직접 고치지 말 것.
    (WEB / "engine-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    page = moved_page()
    (dist / "index.html").write_text(page, encoding="utf-8")
    print(f"dist/index.html (이사 안내, {len(page.encode()) // 1024}KB)")
    build_site(page, dist / "site")


SITE_HEAD = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1F3F94">
<meta http-equiv="refresh" content="0; url={NEW_HOME}">
<link rel="canonical" href="{NEW_HOME}">
<link rel="icon" href="favicon-32.png" sizes="32x32">
<style>
  :root {{ padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
  body {{ margin: 0; }}
</style>
<script>location.replace({json.dumps(NEW_HOME)});</script>
</head>
<body>
"""

SITE_TAIL = """
</body>
</html>
"""

# 예전에 설치된 '먹는거 먼저' 웹앱의 서비스워커를 지운다: 캐시를 비우고 스스로 해제한 뒤 열린 화면을 새로 고쳐 이사 안내(→ 오늘술상)로 보낸다.
SERVICE_WORKER = """self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil((async () => {
  for (const key of await caches.keys()) await caches.delete(key);
  await self.registration.unregister();
  for (const client of await self.clients.matchAll({ type: 'window' })) client.navigate(client.url);
})()));
"""


def build_site(page: str, site: Path) -> None:
    """GitHub Pages(wine-sake-pairing/): 오늘술상으로 바로 넘기고, 못 넘기면 이사 안내를 보여준다."""
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(parents=True)
    (site / "index.html").write_text(SITE_HEAD + page + SITE_TAIL, encoding="utf-8")
    (site / "sw.js").write_text(SERVICE_WORKER, encoding="utf-8")
    for name in ("favicon-32.png",):
        shutil.copy(WEB / "icons" / name, site / name)
    (site / ".nojekyll").write_text("", encoding="utf-8")
    print("dist/site/ (오늘술상으로 이동)")


if __name__ == "__main__":
    main()
