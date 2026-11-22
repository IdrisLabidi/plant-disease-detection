import type { Inferencer, ScanResult } from './types';

export class DeviceInferencer implements Inferencer {
  async predict(): Promise<ScanResult> {
    throw new Error(
      'On-device inference is not available yet. Select Server mode or enable mock mode.',
    );
  }
}
