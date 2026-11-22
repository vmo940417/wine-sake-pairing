import type { BeverageType } from './types';

export const colors = {
  background: '#FAF7F5',
  card: '#FFFFFF',
  text: '#2B1B1F',
  subtext: '#6E5E62',
  border: '#E8DFDC',
  wine: '#7A1F3D',
  sake: '#2F5D8A',
  positive: '#2E7D4F',
  negative: '#B3402A',
  muted: '#F1ECEA',
};

export function scoreColor(score: number): string {
  if (score >= 85) return '#2E7D4F';
  if (score >= 70) return '#6F8F2E';
  if (score >= 55) return '#C08A1E';
  return '#B3402A';
}

const TYPE_COLORS: Record<BeverageType, string> = {
  wine: colors.wine, sake: colors.sake, whisky: '#9A5A12', brandy: '#7A4426', chinese: '#A8321E', korean: '#3F6B3A',
};
const TYPE_LABELS: Record<BeverageType, string> = {
  wine: '🍷 와인', sake: '🍶 사케', whisky: '🥃 위스키', brandy: '🥃 꼬냑', chinese: '🏮 중국술', korean: '🍶 전통주',
};

export const typeColor = (type: BeverageType) => TYPE_COLORS[type];
export const typeLabel = (type: BeverageType) => TYPE_LABELS[type];
