"""규칙 기반 페어링 점수 엔진.

같은 입력이면 항상 같은 점수가 나오도록 LLM 없이 계산한다.
각 규칙은 (가감점, 설명) 을 돌려주고, 기본점에 합산한 뒤 1~99로 자른다.
"""
from app.models import Beverage, Food, Reason

BASE_SCORE = 62.0
MAX_REASONS = 4

SEAFOOD = {"fish", "raw_fish", "shellfish"}

TAG_LABELS = {
    "grilled": "구이", "steak": "스테이크", "lamb": "양고기", "hard_cheese": "숙성 치즈",
    "pork": "돼지고기", "roast": "로스트", "mushroom": "버섯", "tomato_sauce": "토마토 소스",
    "duck": "오리", "salmon": "연어", "poultry": "가금류", "soy_sauce": "간장",
    "bbq": "바비큐", "stew": "스튜", "pizza": "피자", "pasta": "파스타", "truffle": "트러플",
    "braised": "조림·찜", "cured_meat": "햄·살라미", "sweet_soy": "달콤한 간장 양념",
    "fried": "튀김", "cream_sauce": "크림 소스", "lobster": "랍스터", "butter": "버터",
    "oyster": "굴", "shellfish": "조개·갑각류", "raw_fish": "회", "fish": "생선",
    "herbs": "허브", "goat_cheese": "염소치즈", "salad": "샐러드", "asian": "아시아 요리",
    "sour": "새콤한 요리", "spicy": "매운 요리", "curry": "커리", "washed_cheese": "워시 치즈",
    "grilled_fish": "생선구이", "vegetable": "채소", "salty_snack": "짭짤한 안주",
    "caviar": "캐비아", "chocolate": "초콜릿", "blue_cheese": "블루치즈", "dessert": "디저트",
    "nuts": "견과류", "foie_gras": "푸아그라", "fruit": "과일", "miso": "된장",
    "sushi": "초밥", "tofu": "두부", "cheese": "치즈", "fermented": "발효 음식",
}


def _weight(b: Beverage, f: Food) -> tuple[float, str] | None:
    diff = b.profile.body - f.profile.intensity
    if abs(diff) <= 0.75:
        return 6, "술과 음식의 무게감이 비슷해 서로를 덮지 않습니다"
    penalty = -5 * (abs(diff) - 0.75)
    if diff > 0:
        return penalty, "술이 음식보다 무거워 음식 맛을 덮을 수 있습니다"
    return penalty, "음식 맛이 강해 술이 묻힐 수 있습니다"


def _acid_vs_fat(b: Beverage, f: Food) -> tuple[float, str] | None:
    if f.profile.fat < 3:
        return None
    delta = (b.profile.acidity - 3) * f.profile.fat * 0.9
    if delta > 0:
        return delta, "높은 산도가 기름진 맛을 씻어줍니다"
    if delta < 0:
        return delta, "산도가 낮아 기름진 맛이 입에 남습니다"
    return None


def _food_acid(b: Beverage, f: Food) -> tuple[float, str] | None:
    gap = f.profile.acid - b.profile.acidity
    if gap > 0.5:
        return -gap * 5, "음식의 신맛이 술보다 강해 술이 밋밋하게 느껴집니다"
    if f.profile.acid >= 2.5 and b.profile.acidity >= f.profile.acid:
        return 4, "술의 산도가 음식의 신맛을 받쳐줍니다"
    return None


def _tannin(b: Beverage, f: Food) -> tuple[float, str] | None:
    t = b.profile.tannin
    if t < 1:
        return None
    if f.protein == "red_meat":
        return t * (f.profile.fat / 5) * 3.5, "탄닌이 붉은 고기의 단백질·지방과 만나 부드러워집니다"
    if f.protein == "pork":
        return t * (f.profile.fat / 5) * 1.5, "탄닌이 돼지고기의 기름기를 잡아줍니다"
    if f.protein in SEAFOOD:
        return -t * 3.5, "탄닌이 해산물과 만나면 비리고 금속성 맛이 납니다"
    return None


def _tannin_vs_cream(b: Beverage, f: Food) -> tuple[float, str] | None:
    if b.profile.tannin >= 2 and "cream_sauce" in f.tags:
        return -b.profile.tannin * 2.5, "탄닌이 크림소스와 부딪혀 떫게 느껴집니다"
    return None


def _tannin_vs_spice_bitter(b: Beverage, f: Food) -> tuple[float, str] | None:
    t = b.profile.tannin
    if t < 1:
        return None
    delta = -t * f.profile.spice * 0.5 - t * max(0, f.profile.bitter - 1) * 0.6
    if delta <= -2:
        return delta, "매운맛·쓴맛이 탄닌의 떫은맛을 키웁니다"
    return None


def _spice(b: Beverage, f: Food) -> tuple[float, str] | None:
    if f.profile.spice < 2:
        return None
    sweet = (min(b.profile.sweetness, 3) - 1) * f.profile.spice * 0.9
    alcohol = -max(0.0, b.profile.alcohol - 3) * f.profile.spice * 1.2
    delta = sweet + alcohol
    if delta > 0:
        return delta, "적당한 단맛과 낮은 알코올이 매운맛을 진정시킵니다"
    if alcohol < sweet:
        return delta, "높은 알코올이 매운맛을 더 뜨겁게 만듭니다"
    return delta, "단맛이 부족해 매운맛이 그대로 느껴집니다"


def _food_sweetness(b: Beverage, f: Food) -> tuple[float, str] | None:
    gap = f.profile.sweet - b.profile.sweetness
    if gap > 1.5:
        return -(gap - 1.5) * 6, "음식이 술보다 달아 술이 시고 쓰게 느껴집니다"
    if f.profile.sweet >= 3.5 and gap <= 0.5:
        return 6, "술이 음식만큼 달아 디저트와 조화를 이룹니다"
    # 짠 블루치즈·푸아그라는 스위트 와인의 고전 조합이라 예외
    excess = -gap - 1.5
    if excess > 0 and f.protein != "cheese" and "foie_gras" not in f.tags:
        return -excess * 5, "술이 너무 달아 식사 요리와 겉돕니다"
    return None


def _umami(b: Beverage, f: Food) -> tuple[float, str] | None:
    reasons = []
    delta = 0.0
    if b.profile.umami >= 2 and f.profile.umami >= 3:
        delta += b.profile.umami * f.profile.umami * 0.35
        reasons.append("술과 음식의 감칠맛이 서로를 끌어올립니다")
    if b.profile.tannin >= 2 and f.profile.umami > 3:
        delta -= b.profile.tannin * (f.profile.umami - 3) * 1.5
        reasons.append("강한 감칠맛이 탄닌을 더 쓰게 만듭니다")
    if not reasons:
        return None
    return delta, reasons[0] if delta >= 0 else reasons[-1]


def _salt(b: Beverage, f: Food) -> tuple[float, str] | None:
    if f.profile.salt < 3:
        return None
    k = f.profile.salt - 2
    delta = (b.profile.acidity - 2.5) * k + (b.profile.sweetness * k * 0.6 if f.profile.salt >= 4 else 0)
    if delta > 1:
        return delta, "짠맛이 술의 산도·단맛과 균형을 이룹니다"
    return None


def _oak(b: Beverage, f: Food) -> tuple[float, str] | None:
    if b.profile.oak < 2.5:
        return None
    if f.profile.intensity <= 2.5:
        return -(b.profile.oak - 2) * (3 - f.profile.intensity) * 2.5, "오크 향이 섬세한 음식을 덮습니다"
    if {"grilled", "bbq", "steak"} & set(f.tags):
        return b.profile.oak * 1.2, "오크의 훈연·토스트 향이 불향과 어울립니다"
    return None


def _classic(b: Beverage, f: Food) -> tuple[float, str] | None:
    matched = [t for t in b.pairs_with if t in f.tags]
    if not matched:
        return None
    labels = ", ".join(TAG_LABELS.get(t, t) for t in matched[:3])
    return min(len(matched) * 7, 14), f"검증된 조합: {labels}"


RULES = [
    _weight, _acid_vs_fat, _food_acid, _tannin, _tannin_vs_cream, _tannin_vs_spice_bitter,
    _spice, _food_sweetness, _umami, _salt, _oak, _classic,
]


def score_pairing(beverage: Beverage, food: Food) -> tuple[int, list[Reason]]:
    total = BASE_SCORE
    reasons: list[Reason] = []
    for rule in RULES:
        hit = rule(beverage, food)
        if hit is None:
            continue
        delta, text = hit
        total += delta
        if abs(delta) >= 1:
            reasons.append(Reason(text=text, impact=round(delta, 1)))
    reasons.sort(key=lambda r: abs(r.impact), reverse=True)
    return max(1, min(99, round(total))), reasons[:MAX_REASONS]
