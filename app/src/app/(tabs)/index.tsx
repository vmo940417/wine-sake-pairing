import { router, useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Keyboard, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { Chip } from '../../components/ui';
import { api } from '../../lib/api';
import { getRecentFoods } from '../../lib/storage';
import { colors } from '../../lib/theme';
import type { Food } from '../../lib/types';

const SUGGESTIONS = ['삼겹살', '스테이크', '광어회', '초밥', '떡볶이', '후라이드 치킨', '토마토 파스타', '된장찌개'];

export default function PairingHome() {
  const [query, setQuery] = useState('');
  const [matches, setMatches] = useState<Food[]>([]);
  const [recent, setRecent] = useState<string[]>([]);

  useFocusEffect(
    useCallback(() => {
      getRecentFoods().then(setRecent);
    }, []),
  );

  // 입력이 잠시 멈추면 자동완성 후보를 불러온다.
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setMatches([]);
      return;
    }
    const timer = setTimeout(() => {
      api.searchFoods(q).then(setMatches).catch(() => setMatches([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const submit = (food: string) => {
    const value = food.trim();
    if (!value) return;
    Keyboard.dismiss();
    setMatches([]);
    router.push({ pathname: '/pairing', params: { food: value } });
  };

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>어떤 음식을 드시나요?</Text>
      <Text style={styles.subtitle}>음식을 입력하면 어울리는 와인 품종과 사케를 점수 순으로 보여드려요.</Text>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={setQuery}
          placeholder="예: 양념갈비, 트러플 크림 뇨끼"
          placeholderTextColor={colors.subtext}
          returnKeyType="search"
          onSubmitEditing={() => submit(query)}
        />
        <Pressable style={styles.button} onPress={() => submit(query)}>
          <Text style={styles.buttonText}>찾기</Text>
        </Pressable>
      </View>

      {matches.length > 0 && (
        <View style={styles.dropdown}>
          {matches.map((f) => (
            <Pressable key={f.id} style={styles.option} onPress={() => submit(f.name_ko)}>
              <Text style={styles.optionText}>{f.name_ko}</Text>
              <Text style={styles.optionMeta}>{f.cuisine}</Text>
            </Pressable>
          ))}
        </View>
      )}

      {recent.length > 0 && (
        <>
          <Text style={styles.heading}>최근 검색</Text>
          <View style={styles.chips}>
            {recent.slice(0, 8).map((f) => <Chip key={f} label={f} onPress={() => submit(f)} />)}
          </View>
        </>
      )}

      <Text style={styles.heading}>이런 음식은 어때요?</Text>
      <View style={styles.chips}>
        {SUGGESTIONS.map((f) => <Chip key={f} label={f} onPress={() => submit(f)} />)}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 40 },
  title: { fontSize: 24, fontWeight: '800', color: colors.text, marginTop: 8 },
  subtitle: { fontSize: 14, color: colors.subtext, marginTop: 6, marginBottom: 18, lineHeight: 20 },
  inputRow: { flexDirection: 'row', gap: 8 },
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
  dropdown: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    marginTop: 6,
    overflow: 'hidden',
  },
  option: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  optionText: { color: colors.text, fontSize: 15 },
  optionMeta: { color: colors.subtext, fontSize: 13 },
  heading: { fontSize: 15, fontWeight: '700', color: colors.text, marginTop: 24, marginBottom: 10 },
  chips: { flexDirection: 'row', flexWrap: 'wrap' },
});
