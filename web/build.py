"""휴대폰 브라우저용 단일 HTML 빌드.

서버의 데이터(JSON)와 키워드 표를 그대로 넣고, 브라우저 엔진(engine.js)이
Python 엔진과 같은 점수를 내는지 확인한 뒤 dist/index.html 을 만든다.

    python3 web/build.py
"""
import json
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

    html = (WEB / "template.html").read_text(encoding="utf-8")
    html = html.replace("/*__ENGINE__*/", (WEB / "engine.js").read_text(encoding="utf-8"))
    # </script> 가 데이터 안에 들어가도 스크립트가 끊기지 않게 이스케이프
    html = html.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (dist / "index.html").write_text(html, encoding="utf-8")
    print(f"dist/index.html ({len(html.encode()) // 1024}KB)")


if __name__ == "__main__":
    main()
