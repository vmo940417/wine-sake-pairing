import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';

import { ScoreCard } from '../components/ScoreCard';
import { Chip, ErrorView, Loading } from '../components/ui';
import { api } from '../lib/api';
import { addRecentFood } from '../lib/storage';
import { colors } from '../lib/theme';
import type { BeverageType, PairingResponse } from '../lib/types';

type Filter = 'all' | BeverageType;

const SOURCE_NOTE: Record<PairingResponse['food_source'], string | null> = {
  db: null,
  ai: 'AI가 음식의 맛을 추정해 계산했어요.',
  keyword: '등록되지 않은 음식이라 이름으로 맛을 추정했어요. 결과가 대략적일 수 있습니다.',
};

export default function PairingResultScreen() {
  const { food } = useLocalSearchParams<{ food: string }>();
  const [data, setData] = useState<PairingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('all');

  const load = useCallback(() => {
    if (!food) return;
    setError(null);
    setData(null);
    api.pairing(food)
      .then((res) => {
        setData(res);
        addRecentFood(food);
      })
      .catch((e: Error) => setError(e.message));
  }, [food]);

  useEffect(load, [load]);

  const results = useMemo(
    () => (data?.results ?? []).filter((r) => filter === 'all' || r.type === filter),
    [data, filter],
  );

  if (error) return <ErrorView message={`결과를 불러오지 못했습니다.\n${error}`} onRetry={load} />;
  if (!data) return <Loading />;

  const note = SOURCE_NOTE[data.food_source];

  return (
    <>
      <Stack.Screen options={{ title: data.food.name_ko }} />
      <FlatList
        contentContainerStyle={styles.container}
        data={results}
        keyExtractor={(r) => r.beverage_id}
        ListHeaderComponent={
          <View>
            {note && <Text style={styles.note}>{note}</Text>}
            <View style={styles.chips}>
              <Chip label="전체" active={filter === 'all'} onPress={() => setFilter('all')} />
              <Chip label="🍷 와인" active={filter === 'wine'} onPress={() => setFilter('wine')} />
              <Chip label="🍶 사케" active={filter === 'sake'} onPress={() => setFilter('sake')} />
            </View>
          </View>
        }
        renderItem={({ item, index }) => (
          <ScoreCard
            rank={index + 1}
            result={item}
            onPress={() =>
              router.push({ pathname: '/beverage/[id]', params: { id: item.beverage_id, food: data.food.name_ko } })
            }
          />
        )}
      />
    </>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 40 },
  note: {
    backgroundColor: colors.muted,
    color: colors.subtext,
    padding: 10,
    borderRadius: 10,
    fontSize: 13,
    marginBottom: 12,
    lineHeight: 18,
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 4 },
});
