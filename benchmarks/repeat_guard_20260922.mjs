import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  return value;
}

export function createGuard(mode = 'guard') {
  const counts = new Map();
  return (name, input, artifact) => {
    if (name !== 'powershell') return { count: 0, block: false, terminate: false };
    const key = JSON.stringify([name, canonical(input), artifact]);
    const count = (counts.get(key) || 0) + 1;
    counts.set(key, count);
    return { count, block: mode === 'guard' && count > 3, terminate: mode === 'guard' && count > 4 };
  };
}

export default function repeatGuard(pi) {
  const mode = process.env.LAB_LOOP_MODE;
  const log = process.env.LAB_LOOP_LOG;
  if (!['guard', 'observe'].includes(mode) || !log) throw new Error('Missing lab guard configuration');
  const append = row => fs.appendFileSync(log, JSON.stringify({ timestamp: Date.now(), ...row }) + '\n');
  const decide = createGuard(mode);
  append({ event: 'ready', mode });
  pi.on('tool_call', event => {
    if (event.toolName !== 'powershell') return;
    const file = path.join(process.cwd(), 'solution.py');
    const digest = fs.existsSync(file) ? crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex') : 'missing';
    const decision = decide(event.toolName, event.input, digest);
    append({ event: 'decision', toolCallId: event.toolCallId, input: event.input, artifact: digest, ...decision });
    if (decision.block) return {
      block: true, terminate: decision.terminate,
      reason: decision.terminate
        ? 'Lab repeat guard: the unchanged command was repeated again after a warning. Ending this trial as a loop failure.'
        : 'Lab repeat guard: this exact command already ran three times without a change to solution.py. Examine its previous result. Do not repeat it unchanged; use a different diagnostic, repair the code, or finish with your findings.'
    };
  });
}
