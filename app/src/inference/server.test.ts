import { ServerInferencer } from './server';

describe('server inferencer', () => {
  it('builds multipart data without setting a manual content type', async () => {
    let capturedBody: FormData | undefined;
    const api = {
      request: jest.fn(async (_path: string, init: RequestInit) => {
        capturedBody = init.body as FormData;
        return {
          id: '00000000-0000-0000-0000-000000000001',
          source: 'server',
          model_name: 'resnet50',
          model_version: 'test',
          top3: [{ class_name: 'tomato__healthy', probability: 0.8 }],
          unsure: false,
          lesion_area_frac: null,
          mask_url: null,
          latency_ms: 42,
        };
      }),
      requestBinary: jest.fn(),
    };
    const inferencer = new ServerInferencer(api as never);

    await inferencer.predict('file:///tmp/leaf.jpg', {
      model: 'resnet50',
      segment: false,
    });

    expect(capturedBody).toBeInstanceOf(FormData);
    expect(capturedBody?.get('model')).toBe('resnet50');
    expect(capturedBody?.get('segment')).toBe('false');
  });
});
