import fs from 'node:fs';
import path from 'node:path';

import adviceData from './advice.json';

describe('bundled class list', () => {
  it('matches configs/classes.yml class names', () => {
    const root = path.resolve(process.cwd(), '..');
    const yaml = fs.readFileSync(path.join(root, 'configs/classes.yml'), 'utf8');
    const classSection = yaml.split(/^classes:\s*$/m)[1] ?? '';
    const names = classSection
      .split('\n')
      .filter((line) => line.trimStart().startsWith('- '))
      .map((line) =>
        line
          .trim()
          .replace(/^-\s*/, '')
          .replace(/\s+#.*$/, ''),
      );
    const adviceNames = Object.keys(adviceData);
    for (const name of names) {
      expect(adviceNames).toContain(name);
    }
  });
});
