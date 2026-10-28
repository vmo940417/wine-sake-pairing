import { beverages, engine } from './engine';
import type {
  BeverageDetail, BeverageType, DictionaryResponse, Food, PairingResponse, PriceLink,
} from './types';

// 화면 코드는 그대로 두고, 서버 호출 대신 기기 안의 엔진을 쓴다.
const link = (name: string): PriceLink => ({ label: name, url: engine.priceUrl(name) });

function detail(id: string): BeverageDetail | null {
  const b = beverages.find((x) => x.id === id);
  return b ? { ...b, price_links: b.bottles.map(link) } : null;
}

export const api = {
  async searchFoods(q: string): Promise<Food[]> {
    return engine.searchFoods(q);
  },

  async pairing(food: string, type?: BeverageType): Promise<PairingResponse> {
    const res = engine.pair(food);
    return {
      food: res.food,
      food_source: res.source,
      results: res.results
        .filter((r) => !type || r.beverage.type === type)
        .map((r) => ({
          beverage_id: r.beverage.id,
          type: r.beverage.type,
          category: r.beverage.category,
          name_ko: r.beverage.name_ko,
          name_en: r.beverage.name_en,
          score: r.score,
          reasons: r.reasons,
          price_links: r.beverage.bottles.map(link),
        })),
    };
  },

  async beverage(id: string): Promise<BeverageDetail> {
    const b = detail(id);
    if (!b) throw new Error('등록되지 않은 술입니다');
    return b;
  },

  async dictionary(q: string): Promise<DictionaryResponse> {
    const query = q.trim();
    const b = engine.findBeverage(query);
    return {
      query,
      beverage: b ? detail(b.id) : null,
      product: null,
      product_source: null,
      price_link: link(b ? b.name_en : query),
    };
  },
};
