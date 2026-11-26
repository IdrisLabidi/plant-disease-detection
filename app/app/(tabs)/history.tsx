import { useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { z } from 'zod';

import { useAuth } from '@/auth/AuthProvider';
import type { ScanResult } from '@/inference/types';
import { historyItemSchema } from '@/inference/schemas';

const historySchema = z.object({
  items: z.array(historyItemSchema),
  next_cursor: z.string().nullable(),
});

type HistoryItem = z.infer<typeof historyItemSchema>;

export default function HistoryScreen() {
  const { api } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (nextCursor: string | null = null) => {
      if (nextCursor) setLoadingMore(true);
      else setLoading(true);
      setError(null);
      try {
        const query = nextCursor ? `?cursor=${encodeURIComponent(nextCursor)}` : '';
        const payload = historySchema.parse(await api.request<unknown>(`/scans${query}`));
        setItems((current) => (nextCursor ? [...current, ...payload.items] : payload.items));
        setCursor(payload.next_cursor);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'Unable to load history');
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [api],
  );

  useEffect(() => {
    void Promise.resolve().then(() => load());
  }, [load]);

  const remove = async (id: string) => {
    try {
      await api.request(`/scans/${id}`, { method: 'DELETE' });
      setItems((current) => current.filter((item) => item.id !== id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to delete scan');
    }
  };

  const open = (item: HistoryItem) => {
    const result: ScanResult = {
      scanId: item.id,
      source: item.source,
      modelName: item.model_name,
      modelVersion: item.model_version,
      top3: item.top3.map((prediction) => ({
        className: prediction.class_name,
        probability: prediction.probability,
      })),
      unsure: item.unsure,
      lesionAreaFrac: item.lesion_area_frac,
      maskUri: item.mask_url ?? null,
      latencyMs: item.latency_ms ?? 0,
    };
    router.push({
      pathname: '/scan/[id]',
      params: { id: item.id },
    });
  };

  return (
    <View style={styles.page}>
      <Text accessibilityRole="header" style={styles.title}>
        History
      </Text>
      {loading ? <ActivityIndicator accessibilityLabel="Loading scan history" /> : null}
      {error ? (
        <Text accessibilityLiveRegion="polite" style={styles.error}>
          {error}
        </Text>
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <Text>No scans yet. Start by scanning a leaf.</Text>
      ) : null}
      <FlatList
        contentContainerStyle={styles.list}
        data={items}
        keyExtractor={(item) => item.id}
        onEndReached={() => {
          if (cursor && !loadingMore) void load(cursor);
        }}
        onEndReachedThreshold={0.5}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Pressable accessibilityRole="button" onPress={() => open(item)} style={styles.content}>
              <Text style={styles.name}>{item.top_class}</Text>
              <Text>{Math.round(item.confidence * 100)}% confidence</Text>
              <Text>
                {item.source === 'server' ? 'Server' : 'Device'} • {item.model_name} •{' '}
                {item.model_version}
              </Text>
              <Text>{new Date(item.created_at).toLocaleString()}</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => void remove(item.id)}
              style={styles.delete}
            >
              <Text style={styles.deleteText}>Delete</Text>
            </Pressable>
          </View>
        )}
        ListFooterComponent={
          loadingMore ? <ActivityIndicator accessibilityLabel="Loading more scans" /> : undefined
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, padding: 20, width: '100%', maxWidth: 520, alignSelf: 'center' },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 12 },
  list: { gap: 10, paddingBottom: 20 },
  card: { borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 10, overflow: 'hidden' },
  content: { padding: 14, gap: 4, minHeight: 44 },
  name: { fontSize: 18, fontWeight: '700' },
  delete: {
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderTopWidth: 1,
    borderTopColor: '#fecaca',
  },
  deleteText: { color: '#b91c1c', fontWeight: '700' },
  error: { color: '#b91c1c', marginBottom: 8 },
});
