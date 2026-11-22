from typing import Literal

from pydantic import BaseModel, Field

BeverageType = Literal["wine", "sake", "whisky", "brandy", "chinese", "korean"]
Protein = Literal[
    "red_meat", "pork", "poultry", "fish", "raw_fish", "shellfish",
    "vegetable", "cheese", "dessert", "carb",
]


class BeverageProfile(BaseModel):
    """0~5 스케일. 와인·사케를 같은 축으로 표현해야 한 리스트에서 순위를 매길 수 있다."""
    acidity: float
    tannin: float
    body: float
    sweetness: float
    alcohol: float
    umami: float
    aroma: float
    oak: float


class Beverage(BaseModel):
    id: str
    type: BeverageType
    category: str
    abv: float  # 대표 알코올 도수(%)
    name_ko: str
    name_en: str
    aliases: list[str] = []
    profile: BeverageProfile
    summary: str
    regions: list[str] = []
    serving_temp: str
    pairs_with: list[str] = []
    bottles: list[str] = []


class FoodProfile(BaseModel):
    fat: float = Field(ge=0, le=5)
    salt: float = Field(ge=0, le=5)
    acid: float = Field(ge=0, le=5)
    sweet: float = Field(ge=0, le=5)
    umami: float = Field(ge=0, le=5)
    spice: float = Field(ge=0, le=5)
    bitter: float = Field(ge=0, le=5)
    intensity: float = Field(ge=0, le=5)


class Food(BaseModel):
    id: str
    name_ko: str
    aliases: list[str] = []
    cuisine: str = ""
    protein: Protein
    profile: FoodProfile
    tags: list[str] = []


class Reason(BaseModel):
    text: str
    impact: float  # 양수: 가점, 음수: 감점


class PriceLink(BaseModel):
    label: str
    url: str


class PairingResult(BaseModel):
    beverage_id: str
    type: BeverageType
    category: str
    name_ko: str
    name_en: str
    score: int
    reasons: list[Reason]
    price_links: list[PriceLink]


class PairingResponse(BaseModel):
    food: Food
    food_source: Literal["db", "ai", "keyword"]
    results: list[PairingResult]


class BeverageDetail(Beverage):
    price_links: list[PriceLink]


class ProductSummary(BaseModel):
    """LLM이 만든 특정 제품 요약. 사실과 다를 수 있어 화면에 'AI 요약'으로 표시한다."""
    name: str
    type: BeverageType
    producer: str
    region: str
    style: str
    description: str
    food_pairings: list[str]
    related_beverage_id: str | None = None


class DictionaryResponse(BaseModel):
    query: str
    beverage: BeverageDetail | None = None
    product: ProductSummary | None = None
    product_source: Literal["ai"] | None = None
    price_link: PriceLink
