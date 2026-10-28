// 서버 없이 기기 안에서 페어링 점수를 계산한다.
// 엔진(web/engine.js)과 데이터(web/engine-data.json)는 웹 버전과 공유하며,
// `python3 web/build.py` 가 Python 서버 엔진과 결과가 같은지 확인한 뒤 데이터를 생성한다.
import data from '../../../web/engine-data.json';
import type { BeverageDetail, BeverageType, Food, Reason } from './types';

type EngineFood = Food & { profile: Record<string, number> };
type EngineBeverage = Omit<BeverageDetail, 'price_links'>;

type Engine = {
  scorePairing(bev: EngineBeverage, food: EngineFood): { score: number; reasons: Reason[] };
  findFood(query: string): EngineFood | null;
  searchFoods(query: string, limit?: number): EngineFood[];
  findBeverage(query: string): EngineBeverage | null;
  pair(food: string): {
    food: EngineFood;
    source: 'db' | 'keyword';
    results: { beverage: EngineBeverage; score: number; reasons: Reason[] }[];
  };
  priceUrl(name: string): string;
};

// eslint-disable-next-line @typescript-eslint/no-require-imports
const { createEngine } = require('../../../web/engine.js') as { createEngine(d: unknown): Engine };

export const engine = createEngine(data);
export const beverages = data.beverages as unknown as EngineBeverage[];
export type { BeverageType };
