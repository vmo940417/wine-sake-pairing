import { router } from 'expo-router';
import { useState } from 'react';
import { Keyboard, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { PriceButton, PriceNotice } from '../../components/PriceButton';
import { Chip, ErrorView, Loading, Section } from '../../components/ui';
import { api } from '../../lib/api';
import { colors, typeColor, typeLabel } from '../../lib/theme';
import type { DictionaryResponse } from '../../lib/types';

const EXAMPLES = ['피노 누아', '바롤로', '다이긴조', '기모토', 'Dassai 23', 'Opus One'];

export default function DictionaryScreen() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<DictionaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = (q: string) => {
    const value = q.trim();
    if (!value) return;
    Keyboard.dismiss();
    setQuery(value);
    setLoading(true);
    setError(null);
    api.dictionary(value)
      .then(setResult)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={setQuery}
          placeholder="품종, 사케 등급, 제품명"
          placeholderTextColor={colors.subtext}
          returnKeyType="search"
          onSubmitEditing={() => search(query)}
        />
        <Pressable style={styles.button} onPress={() => search(query)}>
          <Text style={styles.buttonText}>검색</Text>
        </Pressable>
      </View>

      {!result && !loading && (
        <View style={styles.chips}>
          {EXAMPLES.map((q) => <Chip key={q} label={q} onPress={() => search(q)} />)}
        </View>
      )}

      {loading && <Loading />}
      {error && <ErrorView message={error} onRetry={() => search(query)} />}
      {result && !loading && <DictionaryResult result={result} />}
    </ScrollView>
  );
}

function DictionaryResult({ result }: { result: DictionaryResponse }) {
  const { beverage, product, price_link } = result;
  return (
    <View style={{ marginTop: 16 }}>
      {product && (
        <Section title={product.name}>
          <Text style={styles.aiBadge}>AI 요약 · 사실과 다를 수 있어요</Text>
          <Text style={[styles.type, { color: typeColor(product.type) }]}>
            {typeLabel(product.type)} · {product.style}
          </Text>
          <Text style={styles.meta}>{[product.producer, product.region].filter(Boolean).join(' · ')}</Text>
          <Text style={styles.body}>{product.description}</Text>
          {product.food_pairings.length > 0 && (
            <Text style={styles.meta}>어울리는 음식: {product.food_pairings.join(', ')}</Text>
          )}
        </Section>
      )}

      {beverage && (
        <Section title={product ? '관련 품종·유형' : beverage.name_ko}>
          <Text style={[styles.type, { color: typeColor(beverage.type) }]}>
            {typeLabel(beverage.type)} · {beverage.category} · {beverage.name_en}
          </Text>
          <Text style={styles.body}>{beverage.summary}</Text>
          <Text style={styles.meta}>대표 산지: {beverage.regions.join(', ')}</Text>
          <Text style={styles.meta}>음용 온도: {beverage.serving_temp}</Text>
          <Pressable onPress={() => router.push({ pathname: '/beverage/[id]', params: { id: beverage.id } })}>
            <Text style={styles.link}>맛 프로파일·대표 제품 보기 →</Text>
          </Pressable>
        </Section>
      )}

      {!beverage && !product && (
        <Section title={result.query}>
          <Text style={styles.body}>
            등록된 품종·유형이 아닙니다. 제품명이라면 아래에서 Wine-Searcher 정보를 확인해 보세요.
          </Text>
        </Section>
      )}

      <Section title="평균가격">
        <PriceButton link={price_link} />
        <PriceNotice />
      </Section>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 40 },
  inputRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  input: {
    flex: 1,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  button: { backgroundColor: colors.wine, borderRadius: 12, paddingHorizontal: 18, justifyContent: 'center' },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  chips: { flexDirection: 'row', flexWrap: 'wrap' },
  aiBadge: { alignSelf: 'flex-start', fontSize: 11, color: colors.subtext, backgroundColor: colors.muted, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginBottom: 8, overflow: 'hidden' },
  type: { fontSize: 13, fontWeight: '600', marginBottom: 4 },
  meta: { fontSize: 13, color: colors.subtext, marginTop: 4, lineHeight: 18 },
  body: { fontSize: 15, color: colors.text, lineHeight: 22, marginTop: 6 },
  link: { color: colors.wine, fontWeight: '600', marginTop: 12 },
});
