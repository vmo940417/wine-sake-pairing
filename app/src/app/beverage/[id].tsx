import { Stack, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { FlavorBars } from '../../components/FlavorBars';
import { PriceButton, PriceNotice } from '../../components/PriceButton';
import { ReasonLine } from '../../components/ScoreCard';
import { ErrorView, Loading, Section } from '../../components/ui';
import { api } from '../../lib/api';
import { getFavorites, toggleFavorite } from '../../lib/storage';
import { colors, scoreColor, typeColor, typeLabel } from '../../lib/theme';
import type { BeverageDetail, PairingResult } from '../../lib/types';

export default function BeverageScreen() {
  const { id, food } = useLocalSearchParams<{ id: string; food?: string }>();
  const [beverage, setBeverage] = useState<BeverageDetail | null>(null);
  const [pairing, setPairing] = useState<PairingResult | null>(null);
  const [favorite, setFavorite] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    api.beverage(id).then(setBeverage).catch((e: Error) => setError(e.message));
    getFavorites().then((list) => setFavorite(list.some((f) => f.id === id)));
    if (food) {
      api.pairing(food, undefined)
        .then((res) => setPairing(res.results.find((r) => r.beverage_id === id) ?? null))
        .catch(() => setPairing(null));
    }
  }, [id, food]);

  useEffect(load, [load]);

  if (error) return <ErrorView message={error} onRetry={load} />;
  if (!beverage) return <Loading />;

  const onToggleFavorite = async () => {
    setFavorite(await toggleFavorite({ id: beverage.id, name_ko: beverage.name_ko, category: beverage.category }));
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Stack.Screen
        options={{
          title: beverage.name_ko,
          headerRight: () => (
            <Pressable onPress={onToggleFavorite} hitSlop={10}>
              <Text style={{ fontSize: 22 }}>{favorite ? '★' : '☆'}</Text>
            </Pressable>
          ),
        }}
      />
      <Text style={[styles.type, { color: typeColor(beverage.type) }]}>
        {typeLabel(beverage.type)} · {beverage.category}
      </Text>
      <Text style={styles.name}>{beverage.name_ko}</Text>
      <Text style={styles.nameEn}>{beverage.name_en}</Text>
      <Text style={styles.summary}>{beverage.summary}</Text>

      {pairing && food && (
        <Section title={`궁합 점수 · ${food}`}>
          <View style={styles.scoreRow}>
            <Text style={[styles.bigScore, { color: scoreColor(pairing.score) }]}>{pairing.score}점</Text>
          </View>
          {pairing.reasons.map((r) => <ReasonLine key={r.text} text={r.text} impact={r.impact} />)}
        </Section>
      )}

      <Section title="맛 프로파일">
        <FlavorBars profile={beverage.profile} type={beverage.type} />
      </Section>

      <Section title="기본 정보">
        <Info label="대표 산지" value={beverage.regions.join(', ')} />
        <Info label="음용 온도" value={beverage.serving_temp} />
      </Section>

      <Section title="대표 제품 평균가격">
        {beverage.price_links.map((link) => <PriceButton key={link.url} link={link} />)}
        <PriceNotice />
      </Section>
    </ScrollView>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 40 },
  type: { fontSize: 13, fontWeight: '600' },
  name: { fontSize: 24, fontWeight: '800', color: colors.text, marginTop: 4 },
  nameEn: { fontSize: 14, color: colors.subtext, marginBottom: 10 },
  summary: { fontSize: 15, lineHeight: 22, color: colors.text, marginBottom: 16 },
  scoreRow: { flexDirection: 'row', alignItems: 'baseline', marginBottom: 6 },
  bigScore: { fontSize: 28, fontWeight: '800' },
  infoRow: { flexDirection: 'row', marginBottom: 6 },
  infoLabel: { width: 72, color: colors.subtext, fontSize: 14 },
  infoValue: { flex: 1, color: colors.text, fontSize: 14, lineHeight: 20 },
});
