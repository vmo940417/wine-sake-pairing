import type {
  BeverageDetail, BeverageType, DictionaryResponse, Food, PairingResponse,
} from './types';

// 실기기에서 테스트할 때는 .env 에 EXPO_PUBLIC_API_URL=http://<PC의 내부 IP>:8000 을 넣는다.
const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

async function get<T>(path: string, params: Record<string, string | undefined> = {}): Promise<T> {
  const query = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v as string)}`)
    .join('&');
  const res = await fetch(`${BASE_URL}${path}${query ? `?${query}` : ''}`);
  if (!res.ok) {
    throw new Error(`서버 오류 (${res.status})`);
  }
  return (await res.json()) as T;
}

export const api = {
  searchFoods: (q: string) => get<Food[]>('/foods/search', { q }),
  pairing: (food: string, type?: BeverageType) =>
    get<PairingResponse>('/pairing', { food, type, limit: '40' }),
  beverage: (id: string) => get<BeverageDetail>(`/beverages/${encodeURIComponent(id)}`),
  dictionary: (q: string) => get<DictionaryResponse>('/dictionary', { q }),
};
