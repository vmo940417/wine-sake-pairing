"""DB에 없는 음식을 키워드로 대략 분석한다. LLM을 쓸 수 없을 때의 대체 경로."""
from app.models import Food, FoodProfile

# (키워드, 단백질, 태그, 맛 프로파일 보정)
KEYWORDS: list[tuple[tuple[str, ...], str | None, list[str], dict[str, float]]] = [
    (("소고기", "한우", "스테이크", "등심", "안심", "차돌", "우삼겹", "소갈비", "소고기"), "red_meat", ["steak"], {"fat": 1.5, "intensity": 1}),
    (("양고기", "양갈비", "램"), "red_meat", ["lamb"], {"fat": 1.5, "intensity": 1.5}),
    (("돼지", "삼겹", "목살", "항정", "돈", "베이컨", "햄"), "pork", ["pork"], {"fat": 2}),
    (("닭", "치킨", "오리", "칠면조"), "poultry", ["poultry"], {"fat": 0.5}),
    (("회", "사시미", "육회", "타다키"), "raw_fish", ["raw_fish"], {"intensity": -1.5, "fat": -0.5}),
    (("연어",), "fish", ["salmon"], {"fat": 1.5}),
    (("생선", "고등어", "갈치", "꽁치", "삼치", "도미", "농어", "대구", "광어"), "fish", ["fish", "grilled_fish"], {}),
    (("새우", "게", "랍스터", "조개", "굴", "가리비", "전복", "오징어", "문어", "낙지", "쭈꾸미", "해물", "해삼"), "shellfish", ["shellfish"], {}),
    (("치즈",), "cheese", ["cheese"], {"fat": 2, "salt": 1.5, "umami": 1.5}),
    (("케이크", "초콜릿", "디저트", "아이스크림", "마카롱", "쿠키", "빵", "타르트", "푸딩"), "dessert", ["dessert"], {"sweet": 3, "salt": -1.5, "umami": -2}),
    (("두부",), "vegetable", ["tofu"], {"intensity": -1}),
    (("버섯", "트러플"), "vegetable", ["mushroom"], {"umami": 1.5}),
    (("샐러드", "채소", "야채", "나물"), "vegetable", ["salad", "vegetable"], {"acid": 1.5, "intensity": -1.5, "fat": -1}),
    (("국수", "면", "밥", "떡"), "carb", [], {}),
    # 조리법·양념
    (("매운", "매콤", "고추장", "고춧가루", "불닭", "마라", "떡볶이", "짬뽕", "김치"), None, ["spicy", "asian"], {"spice": 3.5, "intensity": 1}),
    (("튀김", "까스", "카츠", "프라이", "파전", "부침", "커틀릿"), None, ["fried"], {"fat": 2}),
    (("구이", "숯불", "바비큐", "bbq", "그릴"), None, ["grilled"], {"intensity": 0.5, "bitter": 0.5}),
    (("훈제", "스모크"), None, ["smoked"], {"intensity": 1, "salt": 0.5}),
    (("찜", "조림", "수육", "탕", "전골", "스튜"), None, ["braised"], {"umami": 1}),
    (("간장", "데리야끼", "양념", "불고기", "갈비"), None, ["sweet_soy"], {"sweet": 2, "salt": 1, "umami": 1}),
    (("된장", "미소", "청국장"), None, ["miso", "fermented"], {"umami": 2, "salt": 1.5}),
    (("굴소스", "오이스터"), None, ["soy_sauce", "asian"], {"umami": 1.5, "salt": 0.5}),
    (("크림", "까르보", "버터", "알프레도"), None, ["cream_sauce"], {"fat": 2}),
    (("토마토", "라구", "볼로네제", "피자"), None, ["tomato_sauce"], {"acid": 3, "umami": 1}),
    (("레몬", "초무침", "새콤", "식초", "냉면", "탕수"), None, ["sour"], {"acid": 2.5}),
    (("커리", "카레"), None, ["curry", "spicy", "asian"], {"spice": 2.5, "intensity": 1}),
]

# 이름으로 음식 문화 추정 (같은 지역 술 가점에 쓰임). 먼저 맞는 것이 우선.
CUISINE_HINTS: list[tuple[tuple[str, ...], str]] = [
    (("짜장", "짬뽕", "탕수", "깐풍", "깐쇼", "마라", "훠궈", "딤섬", "샤오롱", "유산슬", "팔보채", "라조", "고추잡채", "양장피",
      "불도장", "춘장", "굴소스", "꿔바로우", "북경", "동파", "중국", "멘보샤", "탄탄", "우육면", "어향", "쯔란", "양꼬치", "꽃빵"), "중식"),
    (("스시", "초밥", "사시미", "라멘", "우동", "소바", "돈부리", "가라아게", "데리야끼", "야키", "오코노미", "타코야키", "미소",
      "규동", "가츠", "카츠", "텐동", "덴푸라", "이자카야", "일본", "오뎅", "샤브"), "일식"),
    (("파스타", "스파게티", "스테이크", "피자", "리조또", "그라탕", "버거", "스튜", "치즈", "감바스", "라자냐", "뇨끼",
      "파에야", "슈니첼", "브런치", "샌드위치", "바게트", "프렌치", "이탈리안"), "양식"),
    (("쌀국수", "팟타이", "똠", "분짜", "나시", "커리", "카레", "탄두리", "반미", "월남쌈", "베트남", "태국", "인도"), "아시아"),
    (("찌개", "국밥", "탕", "전골", "김치", "된장", "고추장", "불고기", "갈비", "삼겹", "족발", "보쌈", "나물", "비빔", "떡",
      "전", "볶음", "조림", "무침", "젓갈", "막걸리", "한식", "곱창", "순대", "닭갈비"), "한식"),
]

BASE = {"fat": 2, "salt": 2.5, "acid": 0.5, "sweet": 1, "umami": 2.5, "spice": 0.5, "bitter": 0.5, "intensity": 3}


def parse_food(name: str) -> Food:
    text = name.lower()
    profile = dict(BASE)
    protein = None
    tags: list[str] = []
    for words, kw_protein, kw_tags, adjust in KEYWORDS:
        if not any(w in text for w in words):
            continue
        if kw_protein and protein is None:
            protein = kw_protein
        tags.extend(t for t in kw_tags if t not in tags)
        for axis, delta in adjust.items():
            profile[axis] += delta
    profile = {k: max(0.0, min(5.0, v)) for k, v in profile.items()}
    cuisine = next((c for words, c in CUISINE_HINTS if any(w in text for w in words)), "")
    return Food(
        id=f"custom:{name}",
        name_ko=name,
        cuisine=cuisine,
        protein=protein or "vegetable",
        profile=FoodProfile(**profile),
        tags=tags,
    )
