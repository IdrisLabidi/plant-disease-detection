import type { Inferencer, ScanResult } from './types';

export class MockInferencer implements Inferencer {
  async predict(
    imageUri: string,
    options: { model: 'resnet50' | 'mobilenet'; segment?: boolean },
  ): Promise<ScanResult> {
    void imageUri;
    await new Promise((resolve) => setTimeout(resolve, 350));
    return {
      source: 'mock',
      modelName: options.model,
      modelVersion: 'mock-1',
      top3: [
        { className: 'tomato__healthy', probability: 0.72 },
        { className: 'tomato__early_blight', probability: 0.18 },
        { className: 'tomato__late_blight', probability: 0.1 },
      ],
      unsure: false,
      lesionAreaFrac: options.segment ? 0.12 : null,
      maskUri: null,
      latencyMs: 350,
    };
  }
}
