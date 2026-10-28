import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { PairingResult } from '../lib/types';
import { colors, scoreColor, typeColor, typeLabel } from '../lib/theme';

type Props = { rank: number; result: PairingResult; onPress: () => void };

export function ScoreCard({ rank, result, onPress }: Props) {
  const [best, ...rest] = result.reasons;
  return (
    <Pressable style={({ pressed }) => [styles.card, pressed && { opacity: 0.7 }]} onPress={onPress}>
      <View style={styles.header}>
        <Text style={styles.rank}>{rank}</Text>
        <View style={{ flex: 1 }}>
          <Text style={[styles.type, { color: typeColor(result.type) }]}>
            {typeLabel(result.type)} · {result.category}
          </Text>
          <Text style={styles.name}>{result.name_ko}</Text>
          <Text style={styles.nameEn}>{result.name_en}</Text>
        </View>
        <View style={[styles.score, { backgroundColor: scoreColor(result.score) }]}>
          <Text style={styles.scoreText}>{result.score}</Text>
          <Text style={styles.scoreUnit}>점</Text>
        </View>
      </View>
      {best && <ReasonLine text={best.text} impact={best.impact} />}
      {rest.slice(0, 1).map((r) => <ReasonLine key={r.text} text={r.text} impact={r.impact} />)}
    </Pressable>
  );
}

export function ReasonLine({ text, impact }: { text: string; impact: number }) {
  const positive = impact >= 0;
  return (
    <Text style={[styles.reason, { color: positive ? colors.positive : colors.negative }]}>
      {positive ? '✓' : '✗'} <Text style={styles.reasonText}>{text}</Text>
    </Text>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colors.border,
  },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 8 },
  rank: { fontSize: 18, fontWeight: '700', color: colors.subtext, width: 24, textAlign: 'center' },
  type: { fontSize: 12, fontWeight: '600' },
  name: { fontSize: 17, fontWeight: '700', color: colors.text, marginTop: 2 },
  nameEn: { fontSize: 12, color: colors.subtext },
  score: { width: 56, height: 56, borderRadius: 28, alignItems: 'center', justifyContent: 'center' },
  scoreText: { color: '#fff', fontSize: 20, fontWeight: '800', lineHeight: 22 },
  scoreUnit: { color: '#fff', fontSize: 10 },
  reason: { fontSize: 13, lineHeight: 19, marginTop: 2 },
  reasonText: { color: colors.text },
});
