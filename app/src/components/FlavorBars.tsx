import { StyleSheet, Text, View } from 'react-native';

import type { BeverageProfile, BeverageType } from '../lib/types';
import { colors, typeColor } from '../lib/theme';

const AXES: { key: keyof BeverageProfile; label: string; wineOnly?: boolean }[] = [
  { key: 'acidity', label: '산도' },
  { key: 'sweetness', label: '당도' },
  { key: 'body', label: '바디' },
  { key: 'tannin', label: '탄닌', wineOnly: true },
  { key: 'umami', label: '감칠맛' },
  { key: 'aroma', label: '향 강도' },
  { key: 'alcohol', label: '알코올' },
  { key: 'oak', label: '오크', wineOnly: true },
];

export function FlavorBars({ profile, type }: { profile: BeverageProfile; type: BeverageType }) {
  const axes = AXES.filter((a) => !(a.wineOnly && type === 'sake'));
  return (
    <View>
      {axes.map(({ key, label }) => (
        <View key={key} style={styles.row}>
          <Text style={styles.label}>{label}</Text>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${(profile[key] / 5) * 100}%`, backgroundColor: typeColor(type) }]} />
          </View>
          <Text style={styles.value}>{profile[key].toFixed(1)}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 10 },
  label: { width: 52, fontSize: 13, color: colors.subtext },
  track: { flex: 1, height: 8, borderRadius: 4, backgroundColor: colors.muted, overflow: 'hidden' },
  fill: { height: 8, borderRadius: 4 },
  value: { width: 28, fontSize: 12, color: colors.subtext, textAlign: 'right' },
});
