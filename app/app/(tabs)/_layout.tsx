import { Redirect, Tabs } from 'expo-router';
import { FontAwesomeIcon } from '@fortawesome/react-native-fontawesome';
import { faClockRotateLeft, faGear, faLeaf } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '@/auth/AuthProvider';

export default function TabsLayout() {
  const { user, restoring } = useAuth();
  if (restoring) return null;
  if (!user) return <Redirect href="/(auth)/login" />;
  return (
    <Tabs>
      <Tabs.Screen name="index" options={{
        title: 'Scan', tabBarIcon(props) {
          return <FontAwesomeIcon icon={faLeaf} size={20} />
        },
      }} />
      <Tabs.Screen name="history" options={{
        title: 'History', tabBarIcon(props) {
          return <FontAwesomeIcon icon={faClockRotateLeft} size={20} />
        }
      }} />
      <Tabs.Screen name="settings" options={{
        title: 'Settings', tabBarIcon(props) {
          return <FontAwesomeIcon icon={faGear} size={20} />
        }
      }} />
    </Tabs>
  );
}
