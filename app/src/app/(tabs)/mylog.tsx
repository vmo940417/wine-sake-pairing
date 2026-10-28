import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Chip, Section } from '../../components/ui';
import { clearRecentFoods, getFavorites, getRecentFoods, type Favorite } from '../../lib/storage';
import { colors } from '../../lib/theme';

export default function MyLogScreen() {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [recent, setRecent] = useState<string[]>([]);

  useFocusEffect(
    useCallback(() => {
      getFavorites().then(setFavorites);
      getRecentFoods().then(setRecent);
    }, []),
  );

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Section title="즐겨찾기한 술">
        {favorites.length === 0 && <Text style={styles.empty}>상세 화면에서 ☆를 눌러 추가하세요.</Text>}
        {favorites.map((f) => (
          <Pressable
            key={f.id}
            style={styles.row}
            onPress={() => router.push({ pathname: '/beverage/[id]', params: { id: f.id } })}
          >
            <Text style={styles.name}>★ {f.name_ko}</Text>
            <Text style={styles.meta}>{f.category}</Text>
          </Pressable>
        ))}
      </Section>

      <Section title="최근 검색한 음식">
        {recent.length === 0 && <Text style={styles.empty}>아직 검색 기록이 없습니다.</Text>}
        <View style={styles.chips}>
          {recent.map((f) => (
            <Chip key={f} label={f} onPress={() => router.push({ pathname: '/pairing', params: { food: f } })} />
          ))}
        </View>
        {recent.length > 0 && (
          <Pressable onPress={() => clearRecentFoods().then(() => setRecent([]))}>
            <Text style={styles.clear}>기록 지우기</Text>
          </Pressable>
        )}
      </Section>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, paddingBottom: 40 },
  empty: { color: colors.subtext, fontSize: 14 },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  name: { color: colors.text, fontSize: 15 },
  meta: { color: colors.subtext, fontSize: 13 },
  chips: { flexDirection: 'row', flexWrap: 'wrap' },
  clear: { color: colors.negative, marginTop: 8, fontSize: 13 },
});
