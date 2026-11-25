import adviceData from './advice.json';
import { adviceSchema, type AdviceEntry } from './adviceSchema';

const advice = adviceSchema.parse(adviceData);

export function getAdvice(className: string): AdviceEntry {
  return (
    advice[className] ?? {
      status: 'placeholder',
      summary: 'No reviewed agronomic advice is available for this result.',
      prevention: ['TODO: team-reviewed prevention guidance'],
      sources: [],
    }
  );
}
