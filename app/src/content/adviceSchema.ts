import { z } from 'zod';

export const adviceEntrySchema = z.object({
  status: z.enum(['placeholder', 'reviewed']),
  summary: z.string(),
  prevention: z.array(z.string()),
  sources: z.array(z.string()),
});

export const adviceSchema = z.record(z.string(), adviceEntrySchema);

export type AdviceEntry = z.infer<typeof adviceEntrySchema>;
