import * as WebBrowser from 'expo-web-browser';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { PriceLink } from '../lib/types';
import { colors } from '../lib/theme';

/** Wine-Searcher 검색 결과를 인앱 브라우저로 연다. 가격은 열람 시점의 최신값이 표시된다. */
export function PriceButton({ link, compact = false }: { link: PriceLink; compact?: boolean }) {
  return (
    <Pressable
      style={({ pressed }) => [styles.button, compact && styles.compact, pressed && styles.pressed]}
      onPress={() => WebBrowser.openBrowserAsync(link.url)}
      accessibilityRole="link"
      accessibilityLabel={`${link.label} 가격을 Wine-Searcher에서 보기`}
    >
      <View style={styles.row}>
        <Text style={styles.label} numberOfLines={1}>{link.label}</Text>
        <Text style={styles.action}>평균가 보기 ↗</Text>
      </View>
    </Pressable>
  );
}

export function PriceNotice() {
  return (
    <Text style={styles.notice}>
      평균가격은 Wine-Searcher에서 조회 시점 기준으로 표시됩니다. 세전 해외 소매가 평균이라 국내 판매가와 차이가 있을 수 있으며, 일부 사케는 등록되어 있지 않을 수 있습니다.
    </Text>
  );
}

const styles = StyleSheet.create({
  button: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 14,
    backgroundColor: colors.card,
    marginBottom: 8,
  },
  compact: { paddingVertical: 8 },
  pressed: { opacity: 0.6 },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  label: { flex: 1, color: colors.text, fontSize: 14 },
  action: { color: colors.wine, fontWeight: '600', fontSize: 13 },
  notice: { color: colors.subtext, fontSize: 12, lineHeight: 17, marginTop: 4 },
});
