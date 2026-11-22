import { z } from 'zod';

import type { ApiClient } from '@/api/client';
import type { Inferencer, ModelName, ScanResult } from './types';

const serverScanSchema = z.object({
  id: z.string(),
  source: z.enum(['server', 'device']),
  model_name: z.enum(['resnet50', 'mobilenet']),
  model_version: z.string(),
  top3: z.array(
    z.object({
      class_name: z.string(),
      probability: z.number().min(0).max(1),
    }),
  ),
  unsure: z.boolean(),
  lesion_area_frac: z.number().min(0).max(1).nullable(),
  mask_url: z.string().nullable().optional(),
  latency_ms: z.number().nullable(),
});

export class ServerInferencer implements Inferencer {
  constructor(private api: ApiClient) {}

  async predict(
    imageUri: string,
    options: { model: ModelName; segment?: boolean },
  ): Promise<ScanResult> {
    const form = new FormData();
    form.append('model', options.model);
    form.append('segment', String(options.segment ?? false));

    if (typeof window !== 'undefined') {
      const blob = await fetch(imageUri).then((response) => response.blob());
      form.append('file', blob, 'scan.jpg');
    } else {
      form.append('file', {
        uri: imageUri,
        name: 'scan.jpg',
        type: 'image/jpeg',
      } as never);
    }

    const payload = await this.api.request<unknown>('/scans', { method: 'POST', body: form });
    const scan = serverScanSchema.parse(payload);
    let maskUri: string | null = null;
    if (scan.mask_url) {
      try {
        const buffer = await this.api.requestBinary(scan.mask_url);
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let index = 0; index < bytes.length; index += 1) {
          binary += String.fromCharCode(bytes[index]);
        }
        maskUri =
          typeof globalThis.btoa === 'function'
            ? `data:image/png;base64,${globalThis.btoa(binary)}`
            : null;
      } catch {
        maskUri = null;
      }
    }
    return {
      scanId: scan.id,
      source: 'server',
      modelName: scan.model_name,
      modelVersion: scan.model_version,
      top3: scan.top3.map((item) => ({
        className: item.class_name,
        probability: item.probability,
      })),
      unsure: scan.unsure,
      lesionAreaFrac: scan.lesion_area_frac,
      maskUri,
      latencyMs: scan.latency_ms ?? 0,
    };
  }
}
