"""가격 확인 링크.

Wine-Searcher 공식 API는 유료라 앱 안에 가격을 직접 표시하지 않고,
사용자가 Wine-Searcher 검색 결과 페이지에서 조회 시점의 최신 평균가를 확인하도록 연결한다.
(스크래핑은 Wine-Searcher 이용약관 위반이라 쓰지 않는다.)
"""
from urllib.parse import quote_plus

from app.models import Beverage, PriceLink

WINE_SEARCHER_FIND = "https://www.wine-searcher.com/find/"


def wine_searcher_url(name: str) -> str:
    terms = "+".join(quote_plus(word) for word in name.lower().split())
    return WINE_SEARCHER_FIND + terms


def link_for(name: str) -> PriceLink:
    return PriceLink(label=name, url=wine_searcher_url(name))


def links_for_beverage(beverage: Beverage) -> list[PriceLink]:
    # 가격은 품종이 아니라 병(제품) 단위로 매겨지므로 대표 병마다 링크를 만든다.
    return [link_for(bottle) for bottle in beverage.bottles]
