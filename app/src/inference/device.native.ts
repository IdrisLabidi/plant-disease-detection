import { Asset } from 'expo-asset';
import * as ImageManipulator from 'expo-image-manipulator';
import { createClassifier, Classifier, SemanticSegmenter, createSemanticSegmenter } from 'react-native-executorch';
import type { SemanticSegmenterOptions, SemanticSegmentationResult, ClassifierOptions } from 'react-native-executorch';

import type { Inferencer, ScanResult } from './types';

const SEGMENTATION_PTE = require('../../assets/models/segmentation.pte');
const CLASSIFICATION_PTE = require('../../assets/models/classification.pte');

const SEGMENTATION_LABELS = ['background', 'plant', 'disease']; // Placeholder ! Example labels, replace with actual labels
const CLASSIFICATION_LABELS = ['healthy', 'diseased']; // Placeholder ! Example labels, replace with actual labels



const SEGMENTATION_OPTIONS: SemanticSegmenterOptions<string> = {
  resizeMode: 'stretch',
  outInterpolation: 'linear',
  interpolation: 'linear',
  normalizeOpts: { alpha: 1 / 255.0, beta: 0.0 }, // Example normalization, replace with actual values
  labels: SEGMENTATION_LABELS,
}; // TODO: Adjust normalization parameters based on the model's training configuration

const CLASSIFICATION_OPTIONS: ClassifierOptions<string> = {
  resizeMode: 'stretch',
  interpolation: 'linear',
  normalizeOpts: { alpha: 1 / 255.0, beta: 0.0 }, // Example normalization, replace with actual values
  labels: CLASSIFICATION_LABELS,
} // TODO: Adjust normalization parameters based on the model's training configuration

export class DeviceInferencer implements Inferencer {
  classifier: Classifier<string> | null = null;
  segmenter: SemanticSegmenter | null = null;

  async initialize() {
    const segAsset = Asset.fromModule(SEGMENTATION_PTE);
    const clsAsset = Asset.fromModule(CLASSIFICATION_PTE);
    await Promise.all([segAsset.downloadAsync(), clsAsset.downloadAsync()]);

    const segSource = segAsset.localUri ?? segAsset.uri;
    const clsSource = clsAsset.localUri ?? clsAsset.uri;

    if (!segSource || !clsSource) {
      throw new Error('Failed to resolve .pte model asset URIs.');
    }

    this.classifier = await createClassifier({
      modelPath: clsSource,
      modelOpts: CLASSIFICATION_OPTIONS
    });

    this.segmenter = await createSemanticSegmenter({
      modelPath: segSource,
      modelOpts: SEGMENTATION_OPTIONS
    });
  }

  //TODO: Implement on-device inference using react-native-executorch
  async predict(): Promise<ScanResult> {
    throw new Error(
      'On-device inference is not available yet. Select Server mode or enable mock mode.',
    );
  }
}
