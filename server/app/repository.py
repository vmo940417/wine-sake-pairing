"""JSON 데이터 로더. 데이터가 커지면 이 모듈만 DB(PostgreSQL 등)로 바꾸면 된다."""
import json
from functools import lru_cache
from pathlib import Path

from app.models import Beverage, Food

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def normalize(text: str) -> str:
    return "".join(text.lower().split())


@lru_cache
def beverages() -> list[Beverage]:
    raw = json.loads((DATA_DIR / "beverages.json").read_text(encoding="utf-8"))
    return [Beverage(**item) for item in raw]


@lru_cache
def foods() -> list[Food]:
    raw = json.loads((DATA_DIR / "foods.json").read_text(encoding="utf-8"))
    return [Food(**item) for item in raw]


def get_beverage(beverage_id: str) -> Beverage | None:
    return next((b for b in beverages() if b.id == beverage_id), None)


def _names(item: Beverage | Food) -> list[str]:
    names = [item.name_ko, *item.aliases]
    if isinstance(item, Beverage):
        names.append(item.name_en)
    return [normalize(n) for n in names]


def find_food(query: str) -> Food | None:
    """정확 일치 → 부분 일치 순으로 찾는다."""
    q = normalize(query)
    if not q:
        return None
    for food in foods():
        if q in _names(food):
            return food
    # 입력 안에 짧은 별칭이 들어 있는 경우("연어 데리야끼" ⊃ "연어")는 다른 요리일 수 있어 3자 이상만 인정한다.
    for food in foods():
        if any(q in n or (len(n) >= 3 and n in q) for n in _names(food)):
            return food
    return None


def search_foods(query: str, limit: int = 8) -> list[Food]:
    q = normalize(query)
    if not q:
        return []
    return [f for f in foods() if any(q in n for n in _names(f))][:limit]


def find_beverage(query: str) -> Beverage | None:
    q = normalize(query)
    if not q:
        return None
    for b in beverages():
        if q in _names(b):
            return b
    for b in beverages():
        if any(len(n) >= 2 and (q in n or n in q) for n in _names(b)):
            return b
    return None
