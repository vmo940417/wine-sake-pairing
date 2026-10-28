import { Tabs } from 'expo-router/js-tabs';
import { Text } from 'react-native';

import { colors } from '../../lib/theme';

const icon = (emoji: string) => () => <Text style={{ fontSize: 20 }}>{emoji}</Text>;

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.wine,
        headerStyle: { backgroundColor: colors.background },
        headerTitleStyle: { color: colors.text, fontWeight: '700' },
        sceneStyle: { backgroundColor: colors.background },
      }}
    >
      <Tabs.Screen name="index" options={{ title: '페어링', tabBarIcon: icon('🍽️') }} />
      <Tabs.Screen name="dictionary" options={{ title: '술 사전', tabBarIcon: icon('📖') }} />
      <Tabs.Screen name="mylog" options={{ title: '내 기록', tabBarIcon: icon('⭐') }} />
    </Tabs>
  );
}
