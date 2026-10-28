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

export const typeColor = (type: 'wine' | 'sake') => (type === 'wine' ? colors.wine : colors.sake);
export const typeLabel = (type: 'wine' | 'sake') => (type === 'wine' ? '🍷 와인' : '🍶 사케');
