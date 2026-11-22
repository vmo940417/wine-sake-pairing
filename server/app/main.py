from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import repository
from app.models import (
    BeverageDetail, BeverageType, DictionaryResponse, Food, PairingResponse,
)
from app.services import llm
from app.services.pairing import pair
from app.services.price_links import link_for, links_for_beverage

app = FastAPI(title="Wine & Sake Pairing API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def _detail(beverage) -> BeverageDetail:
    return BeverageDetail(**beverage.model_dump(), price_links=links_for_beverage(beverage))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "llm_enabled": llm.enabled()}


@app.get("/foods/search", response_model=list[Food])
def search_foods(q: str = Query(min_length=1, max_length=50)):
    """음식 입력창 자동완성."""
    return repository.search_foods(q)


@app.get("/pairing", response_model=PairingResponse)
def get_pairing(
    food: str = Query(min_length=1, max_length=50),
    type: BeverageType | None = None,
    limit: int = Query(20, ge=1, le=60),
):
    """음식 → 와인 품종·사케 유형을 페어링 점수 높은 순으로."""
    return pair(food, type, limit)


@app.get("/beverages", response_model=list[BeverageDetail])
def list_beverages(type: BeverageType | None = None):
    return [_detail(b) for b in repository.beverages() if type is None or b.type == type]


@app.get("/beverages/{beverage_id}", response_model=BeverageDetail)
def get_beverage(beverage_id: str):
    beverage = repository.get_beverage(beverage_id)
    if beverage is None:
        raise HTTPException(404, "등록되지 않은 술입니다")
    return _detail(beverage)


@app.get("/dictionary", response_model=DictionaryResponse)
def dictionary(q: str = Query(min_length=1, max_length=80)):
    """술 사전: 품종·유형 이름이면 내부 DB 설명, 제품명이면 AI 요약 + 가격 확인 링크."""
    query = q.strip()
    beverage = repository.find_beverage(query)
    if beverage is not None:
        return DictionaryResponse(query=query, beverage=_detail(beverage), price_link=link_for(beverage.name_en))

    product = llm.summarize_product(query) if llm.enabled() else None
    related = repository.get_beverage(product.related_beverage_id) if product and product.related_beverage_id else None
    return DictionaryResponse(
        query=query,
        beverage=_detail(related) if related else None,
        product=product,
        product_source="ai" if product else None,
        price_link=link_for(product.name if product else query),
    )
