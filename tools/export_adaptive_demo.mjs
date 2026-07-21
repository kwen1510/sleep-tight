import { createRequire } from 'node:module';
import { writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const require = createRequire(import.meta.url);
const model = require('../computer/adaptive_sleep_model.js');
const output = resolve('computer/data/demo/adaptive-30-night-report.json');
await writeFile(output, `${JSON.stringify(model.buildDataset(), null, 2)}\n`);
console.log(output);
