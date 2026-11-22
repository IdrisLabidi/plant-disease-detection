import { loadConfig } from '@/config';
import type { Inferencer } from './types';
import { MockInferencer } from './mock';
import { ServerInferencer } from './server';
import { DeviceInferencer } from './device';

export function getInferencers(api: import('@/api/client').ApiClient): {
  server: Inferencer;
  device: Inferencer | null;
  mock: Inferencer;
} {
  return {
    server: new ServerInferencer(api),
    device: DeviceInferencer,
    mock: new MockInferencer(),
  };
}

export function getConfiguredInferencer(
  api: import('@/api/client').ApiClient,
  mode: 'auto' | 'server' | 'device',
): Inferencer {
  const config = loadConfig();
  if (config.mock) return new MockInferencer();
  const inferencers = getInferencers(api);
  if (mode === 'device') return inferencers.device ?? inferencers.server;
  if (mode === 'server') return inferencers.server;
  return inferencers.server;
}
