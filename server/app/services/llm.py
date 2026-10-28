"""Claude API 연동: (1) DB에 없는 음식의 맛 프로파일 추정, (2) 특정 제품(병) 요약.

ANTHROPIC_API_KEY 가 없으면 비활성화되고, 호출부는 키워드 분석 등 대체 경로를 쓴다.
"""
import logging
import os
from typing import Literal

import anthropic
from pydantic import BaseModel, ValidationError

from app.engine.scoring import TAG_LABELS
from app.models import BeverageType, Food, FoodProfile, ProductSummary, Protein
from app import repository

log = logging.getLogger(__name__)

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")

_client: anthropic.Anthropic | None = None


def enabled() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _parse(system: str, prompt: str, output_format: type[BaseModel]) -> BaseModel | None:
    try:
        response = _get_client().beta.messages.parse(
            model=MODEL,
            max_tokens=4000,
            # 짧은 분류·요약 작업이라 effort 를 낮춰 비용과 지연을 줄인다.
            output_config={"effort": "low"},
            # 안전 분류기가 거절하면 서버에서 대체 모델로 자동 재시도한다.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_format=output_format,
        )
    except anthropic.APIStatusError as e:
        log.warning("Claude API 오류 %s: %s", e.status_code, e.message)
        return None
    except anthropic.APIConnectionError:
        log.warning("Claude API 연결 실패")
        return None
    except ValidationError as e:
        log.warning("Claude 응답이 스키마와 맞지 않음: %s", e)
        return None
    if response.stop_reason == "refusal":
        log.warning("Claude 가 요청을 거절함: %s", response.stop_details)
        return None
    return response.parsed_output


# ---------- 음식 맛 프로파일 ----------

class _RawFoodProfile(BaseModel):
    # 스키마에 범위를 걸어도 강제되지 않으므로 받은 뒤 0~5로 자른다.
    fat: float
    salt: float
    acid: float
    sweet: float
    umami: float
    spice: float
    bitter: float
    intensity: float


class _FoodAnalysis(BaseModel):
    name_ko: str
    protein: Protein
    profile: _RawFoodProfile
    tags: list[str]


FOOD_SYSTEM = f"""당신은 와인·사케 페어링용 음식 분석가입니다.
음식 이름을 받아 일반적인 조리 방식 기준의 맛 프로파일을 0~5 척도로 추정합니다.
- fat 지방, salt 염도, acid 신맛, sweet 단맛, umami 감칠맛, spice 매운맛, bitter 쓴맛, intensity 전체 풍미 강도
- protein 은 주재료 분류입니다. 회·날생선은 raw_fish, 익힌 생선은 fish, 조개·갑각류·두족류는 shellfish 입니다.
- tags 는 아래 목록에서만 해당하는 것을 0~5개 고르세요: {", ".join(TAG_LABELS)}
- name_ko 는 입력을 정돈한 한국어 음식 이름입니다."""


def analyze_food(name: str) -> Food | None:
    result = _parse(FOOD_SYSTEM, f"음식: {name}", _FoodAnalysis)
    if result is None:
        return None
    return Food(
        id=f"ai:{name}",
        name_ko=result.name_ko,
        protein=result.protein,
        profile=FoodProfile(**{k: max(0.0, min(5.0, v)) for k, v in result.profile.model_dump().items()}),
        tags=[t for t in result.tags if t in TAG_LABELS],
    )


# ---------- 제품 요약 ----------

class _ProductAnalysis(BaseModel):
    recognized: bool
    name: str
    type: BeverageType
    producer: str
    region: str
    style: str
    description: str
    food_pairings: list[str]
    related_beverage_id: str | None


def _product_system() -> str:
    ids = ", ".join(f"{b.id}({b.name_ko})" for b in repository.beverages())
    return f"""당신은 와인·사케 소믈리에입니다. 사용자가 입력한 술 이름(제품명)을 간단히 설명합니다.
- 실제로 알고 있는 제품일 때만 recognized=true 로 답하세요. 모르거나 확신이 없으면 recognized=false 로 두고 나머지는 빈 값으로 둡니다. 지어내지 마세요.
- type 은 wine 또는 sake 입니다.
- style 은 품종·등급·스타일을 짧게 (예: "카베르네 소비뇽 중심 보르도 블렌드", "준마이 다이긴조, 정미보합 45%").
- description 은 맛과 특징을 한국어 2~3문장으로.
- food_pairings 는 어울리는 음식 3~5개(한국어).
- related_beverage_id 는 다음 중 가장 가까운 분류의 id 하나, 없으면 null: {ids}
- 가격은 언급하지 마세요."""


def summarize_product(name: str) -> ProductSummary | None:
    result = _parse(_product_system(), f"술 이름: {name}", _ProductAnalysis)
    if result is None or not result.recognized:
        return None
    related = result.related_beverage_id
    if related and repository.get_beverage(related) is None:
        related = None
    return ProductSummary(
        name=result.name, type=result.type, producer=result.producer, region=result.region,
        style=result.style, description=result.description,
        food_pairings=result.food_pairings, related_beverage_id=related,
    )
