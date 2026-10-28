from functools import lru_cache
from typing import Literal

from app import repository
from app.engine.scoring import score_pairing
from app.models import BeverageType, Food, PairingResponse, PairingResult
from app.services import food_parser, llm
from app.services.price_links import links_for_beverage


@lru_cache(maxsize=512)
def _analyze_unknown(name: str) -> tuple[Food, Literal["ai", "keyword"]]:
    # 같은 음식을 반복 조회할 때 LLM 을 다시 부르지 않도록 캐시한다.
    if llm.enabled():
        food = llm.analyze_food(name)
        if food is not None:
            return food, "ai"
    return food_parser.parse_food(name), "keyword"


def resolve_food(name: str) -> tuple[Food, Literal["db", "ai", "keyword"]]:
    food = repository.find_food(name)
    if food is not None:
        return food, "db"
    return _analyze_unknown(name.strip())


def pair(name: str, beverage_type: BeverageType | None = None, limit: int = 20) -> PairingResponse:
    food, source = resolve_food(name)
    results = []
    for b in repository.beverages():
        if beverage_type and b.type != beverage_type:
            continue
        score, reasons = score_pairing(b, food)
        results.append(PairingResult(
            beverage_id=b.id, type=b.type, category=b.category,
            name_ko=b.name_ko, name_en=b.name_en, score=score, reasons=reasons,
            price_links=links_for_beverage(b),
        ))
    results.sort(key=lambda r: r.score, reverse=True)
    return PairingResponse(food=food, food_source=source, results=results[:limit])
