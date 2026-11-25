import * as ImageManipulator from 'expo-image-manipulator';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '@/auth/AuthProvider';
import { getConfiguredInferencer } from '@/inference';
import type { ModelName } from '@/inference/types';

type ScanMode = 'auto' | 'server' | 'device';

export default function ScanScreen() {
  const { api } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<ScanMode>('server');
  const [model, setModel] = useState<ModelName>('resnet50');
  const [segment, setSegment] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [consentVisible, setConsentVisible] = useState(false);
  const [pendingAction, setPendingAction] = useState<'camera' | 'gallery' | null>(null);

  const chooseMode = (next: ScanMode) => {
    setMode(next);
  };

  const prepareImage = async (uri: string, width: number, height: number) => {
    const resize =
      width >= height ? { width: Math.min(width, 1024) } : { height: Math.min(height, 1024) };
    const result = await ImageManipulator.manipulateAsync(uri, [{ resize }], {
      compress: 0.82,
      format: ImageManipulator.SaveFormat.JPEG,
    });
    return result.uri;
  };

  const runInference = async (uri: string, width: number, height: number) => {
    setLoading(true);
    setError(null);
    try {
      const preparedUri = await prepareImage(uri, width, height);
      const inferencer = getConfiguredInferencer(api, mode);
      const result = await inferencer.predict(preparedUri, { model, segment });
      router.push({
        pathname: '/scan/[id]',
        params: {
          id: result.scanId ?? `local-${Date.now()}`,
          imageUri: preparedUri,
          result: JSON.stringify(result),
        },
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to analyze this image');
    } finally {
      setLoading(false);
    }
  };

  const openPicker = async (kind: 'camera' | 'gallery') => {
    setConsentVisible(false);
    setPendingAction(null);
    if (kind === 'camera') {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        setError('Camera permission is required. Enable it in system settings to take a photo.');
        return;
      }
      const selected = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        quality: 0.9,
        allowsEditing: false,
      });
      if (!selected.canceled && selected.assets[0]) {
        const asset = selected.assets[0];
        await runInference(asset.uri, asset.width, asset.height);
      }
      return;
    }

    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setError(
        'Photo library permission is required. Enable it in system settings to choose a photo.',
      );
      return;
    }
    const selected = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.9,
      allowsEditing: false,
    });
    if (!selected.canceled && selected.assets[0]) {
      const asset = selected.assets[0];
      await runInference(asset.uri, asset.width, asset.height);
    }
  };

  const askConsent = (kind: 'camera' | 'gallery') => {
    setPendingAction(kind);
    setConsentVisible(true);
  };

  return (
    <View style={styles.page}>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.title}>
          Scan a leaf
        </Text>
        <Text style={styles.tip}>Use one leaf, good light, and fill the frame.</Text>
        <Text style={styles.label}>Engine mode</Text>
        <View style={styles.row}>
          {(['auto', 'server', 'device'] as const).map((value) => (
            <Pressable
              accessibilityRole="button"
              key={value}
              onPress={() => chooseMode(value)}
              style={[styles.chip, mode === value && styles.chipActive]}
            >
              <Text>{value}</Text>
            </Pressable>
          ))}
        </View>
        <Text style={styles.label}>Model</Text>
        <View style={styles.row}>
          {(['resnet50', 'mobilenet'] as const).map((value) => (
            <Pressable
              accessibilityRole="button"
              key={value}
              onPress={() => setModel(value)}
              style={[styles.chip, model === value && styles.chipActive]}
            >
              <Text>{value}</Text>
            </Pressable>
          ))}
        </View>
        <Pressable
          accessibilityRole="button"
          onPress={() => setSegment((value) => !value)}
          style={[styles.button, segment && styles.segmentActive]}
        >
          <Text>{segment ? 'Segmentation on' : 'Run segmentation'}</Text>
        </Pressable>
        {error ? (
          <Text accessibilityLiveRegion="polite" style={styles.error}>
            {error}
          </Text>
        ) : null}
        {loading ? <ActivityIndicator accessibilityLabel="Analyzing image" /> : null}
        <Pressable
          accessibilityRole="button"
          disabled={loading}
          onPress={() => askConsent('camera')}
          style={styles.primary}
        >
          <Text style={styles.primaryText}>Take photo</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          disabled={loading}
          onPress={() => askConsent('gallery')}
          style={styles.button}
        >
          <Text>Choose from gallery</Text>
        </Pressable>
      </View>

      <Modal transparent visible={consentVisible} animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text accessibilityRole="header" style={styles.modalTitle}>
              Photo upload consent
            </Text>
            <Text style={styles.tip}>
              Photos may be uploaded and stored to provide inference and scan history. Choose server
              mode to upload, or use device mode when it is available.
            </Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => void openPicker(pendingAction ?? 'gallery')}
              style={styles.primary}
            >
              <Text style={styles.primaryText}>Allow and continue</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => setConsentVisible(false)}
              style={styles.button}
            >
              <Text>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, alignItems: 'center', padding: 20 },
  card: { width: '100%', maxWidth: 520, gap: 12 },
  title: { fontSize: 28, fontWeight: '700' },
  tip: { color: '#475569' },
  label: { fontWeight: '700', marginTop: 4 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    minHeight: 44,
    borderWidth: 1,
    borderColor: '#64748b',
    borderRadius: 22,
    paddingHorizontal: 14,
    justifyContent: 'center',
  },
  chipActive: { backgroundColor: '#dcfce7', borderColor: '#166534' },
  button: {
    minHeight: 48,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#64748b',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  segmentActive: { backgroundColor: '#dcfce7' },
  primary: {
    minHeight: 48,
    borderRadius: 8,
    backgroundColor: '#166534',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  primaryText: { color: '#fff', fontWeight: '700' },
  error: { color: '#b91c1c' },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    gap: 12,
  },
  modalTitle: { fontSize: 20, fontWeight: '700' },
});
