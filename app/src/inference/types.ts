export type InferenceSource = 'server' | 'device';
export type ModelName = 'resnet50' | 'mobilenet';

export type TopPrediction = {
  className: string;
  probability: number;
};

export type ScanResult = {
  scanId?: string;
  source: InferenceSource;
  modelName: ModelName;
  modelVersion: string;
  top3: TopPrediction[];
  unsure: boolean;
  lesionAreaFrac: number | null;
  maskUri: string | null;
  latencyMs: number;
};

export interface Inferencer {
  predict(imageUri: string, options: { model: ModelName; segment?: boolean }): Promise<ScanResult>;
}
