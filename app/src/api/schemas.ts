import { z } from 'zod';

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email().nullable(),
  email_verified: z.boolean(),
  display_name: z.string().nullable(),
  created_at: z.string(),
});

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string().optional(),
  expires_in: z.number(),
  user: userSchema,
  is_new_user: z.boolean().nullable().optional(),
});
