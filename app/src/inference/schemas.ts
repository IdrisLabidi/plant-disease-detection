import { z } from 'zod';

export const historyItemSchema = z.object({
  id: z.string(),
  client_id: z.string().nullable(),
  created_at: z.string(),
  source: z.enum(['server', 'device']),
  model_name: z.enum(['resnet50', 'mobilenet']),
  model_version: z.string(),
  top_class: z.string(),
  confidence: z.number(),
  top3: z.array(
    z.object({
      class_name: z.string(),
      probability: z.number(),
    }),
  ),
  unsure: z.boolean(),
  lesion_area_frac: z.number().nullable(),
  mask_url: z.string().nullable().optional(),
  image_url: z.string().nullable().optional(),
  latency_ms: z.number().nullable(),
  notes: z.string().nullable(),
});