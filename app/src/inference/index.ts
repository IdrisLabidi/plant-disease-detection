import type { Inferencer } from './types';
import { ServerInferencer } from './server';
import { DeviceInferencer } from './device';

export function getInferencers(api: import('@/api/client').ApiClient): {
  server: Inferencer;
  device: Inferencer | null;
} {
  return {
    server: new ServerInferencer(api),
    device: DeviceInferencer,
  };
}

export function getConfiguredInferencer(
  api: import('@/api/client').ApiClient,
  mode: 'auto' | 'server' | 'device',
): Inferencer {
  const inferencers = getInferencers(api);
  if (mode === 'device') return inferencers.device ?? inferencers.server;
  if (mode === 'server') return inferencers.server;
  return inferencers.server;
}
