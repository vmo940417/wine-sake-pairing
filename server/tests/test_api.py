import pytest
from fastapi.testclient import TestClient

from app import repository
from app.engine.scoring import score_pairing
from app.main import app
from app.services import food_parser, llm

client = TestClient(app)


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    monkeypatch.setattr(llm, "enabled", lambda: False)


def top(food: str, n: int = 3) -> list[str]:
    res = client.get("/pairing", params={"food": food}).json()
    return [r["beverage_id"] for r in res["results"][:n]]


@pytest.mark.parametrize("food, expected", [
    ("립아이 스테이크", "cabernet_sauvignon"),
    ("생굴", "chablis"),
    ("후라이드 치킨", "champagne"),
    ("초밥", "sake_junmai_ginjo"),
    ("떡볶이", "sake_nigori"),
    ("마파두부", "riesling_offdry"),
    ("토마토 파스타", "sangiovese"),
    ("초콜릿 케이크", "port"),
    ("샐러드", "sauvignon_blanc"),
])
def test_classic_pairings_rank_near_top(food, expected):
    assert expected in top(food)


def test_tannic_red_scores_low_with_raw_fish():
    cab = repository.get_beverage("cabernet_sauvignon")
    hoe = repository.find_food("광어회")
    score, reasons = score_pairing(cab, hoe)
    assert score < 40
    assert any(r.impact < 0 and "탄닌" in r.text for r in reasons)


def test_results_sorted_and_mix_wine_and_sake():
    res = client.get("/pairing", params={"food": "삼겹살", "limit": 38}).json()
    scores = [r["score"] for r in res["results"]]
    assert scores == sorted(scores, reverse=True)
    assert {r["type"] for r in res["results"]} == {"wine", "sake"}
    assert res["food_source"] == "db"


def test_type_filter():
    res = client.get("/pairing", params={"food": "회", "type": "sake"}).json()
    assert res["results"] and all(r["type"] == "sake" for r in res["results"])


def test_unknown_food_falls_back_to_keywords():
    res = client.get("/pairing", params={"food": "매운 돼지 숯불구이"}).json()
    assert res["food_source"] == "keyword"
    assert res["food"]["protein"] == "pork"
    assert "spicy" in res["food"]["tags"]


def test_short_alias_inside_query_does_not_hijack_dish():
    res = client.get("/pairing", params={"food": "연어 데리야끼"}).json()
    assert res["food_source"] == "keyword"
    assert "sweet_soy" in res["food"]["tags"]
    assert client.get("/pairing", params={"food": "매운 삼겹살"}).json()["food"]["id"] == "samgyeopsal"


def test_keyword_parser_does_not_misread_common_syllables():
    food = food_parser.parse_food("소스 듬뿍 전복 버터구이")
    assert food.protein == "shellfish"
    assert "fried" not in food.tags


def test_price_links_point_to_wine_searcher():
    res = client.get("/beverages/sake_junmai_daiginjo").json()
    urls = [l["url"] for l in res["price_links"]]
    assert "https://www.wine-searcher.com/find/dassai+45" in urls


def test_dictionary_matches_varietal_alias():
    res = client.get("/dictionary", params={"q": "바롤로"}).json()
    assert res["beverage"]["id"] == "nebbiolo"
    assert res["product"] is None


def test_dictionary_unknown_product_without_llm_still_gives_price_link():
    res = client.get("/dictionary", params={"q": "Opus One 2019"}).json()
    assert res["beverage"] is None and res["product"] is None
    assert res["price_link"]["url"] == "https://www.wine-searcher.com/find/opus+one+2019"


def test_food_autocomplete():
    names = [f["name_ko"] for f in client.get("/foods/search", params={"q": "갈비"}).json()]
    assert "소갈비 구이 (양념)" in names


def test_llm_food_analysis_is_clamped_and_tags_filtered(monkeypatch):
    raw = llm._FoodAnalysis(
        name_ko="트러플 크림 뇨끼", protein="vegetable",
        profile=llm._RawFoodProfile(fat=7, salt=2, acid=0, sweet=0, umami=4, spice=-1, bitter=0, intensity=3),
        tags=["cream_sauce", "truffle", "invented_tag"],
    )
    monkeypatch.setattr(llm, "_parse", lambda *a, **k: raw)
    food = llm.analyze_food("트러플 크림 뇨끼")
    assert food.profile.fat == 5 and food.profile.spice == 0
    assert food.tags == ["cream_sauce", "truffle"]


def test_dictionary_uses_llm_summary_when_available(monkeypatch):
    from app.models import ProductSummary
    summary = ProductSummary(
        name="Dassai 23", type="sake", producer="Asahi Shuzo", region="야마구치",
        style="준마이 다이긴조", description="...", food_pairings=["회"],
        related_beverage_id="sake_junmai_daiginjo",
    )
    monkeypatch.setattr(llm, "enabled", lambda: True)
    monkeypatch.setattr(llm, "summarize_product", lambda q: summary)
    res = client.get("/dictionary", params={"q": "닷사이 23"}).json()
    assert res["product_source"] == "ai"
    assert res["beverage"]["id"] == "sake_junmai_daiginjo"
    assert res["price_link"]["url"].endswith("/find/dassai+23")
