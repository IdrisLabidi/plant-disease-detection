import { loadConfig } from './config';

describe('loadConfig', () => {
  it('reads EXPO_PUBLIC_API_URL directly', () => {
    process.env.EXPO_PUBLIC_API_URL = 'http://127.0.0.1:8000';
    process.env.EXPO_PUBLIC_MOCK = '1';

    expect(loadConfig().apiUrl).toBe('http://127.0.0.1:8000');
  });
});
