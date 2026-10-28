import AsyncStorage from '@react-native-async-storage/async-storage';

const RECENT_KEY = 'recent_foods';
const FAVORITES_KEY = 'favorite_beverages';
const MAX_RECENT = 15;

export type Favorite = { id: string; name_ko: string; category: string };

async function read<T>(key: string, fallback: T): Promise<T> {
  try {
    const raw = await AsyncStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

async function write(key: string, value: unknown): Promise<void> {
  try {
    await AsyncStorage.setItem(key, JSON.stringify(value));
  } catch {
    // 저장 실패는 앱 동작에 영향이 없으므로 무시한다.
  }
}

export async function getRecentFoods(): Promise<string[]> {
  return read<string[]>(RECENT_KEY, []);
}

export async function addRecentFood(food: string): Promise<void> {
  const recent = await getRecentFoods();
  const next = [food, ...recent.filter((f) => f !== food)].slice(0, MAX_RECENT);
  await write(RECENT_KEY, next);
}

export async function clearRecentFoods(): Promise<void> {
  await write(RECENT_KEY, []);
}

export async function getFavorites(): Promise<Favorite[]> {
  return read<Favorite[]>(FAVORITES_KEY, []);
}

export async function toggleFavorite(item: Favorite): Promise<boolean> {
  const favorites = await getFavorites();
  const exists = favorites.some((f) => f.id === item.id);
  await write(FAVORITES_KEY, exists ? favorites.filter((f) => f.id !== item.id) : [item, ...favorites]);
  return !exists;
}
