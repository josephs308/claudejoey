/**
 * Sends a correctly signed test webhook at a running connector, so you can
 * verify signature handling and the sync path without waiting on Lawmatics.
 *
 *   npx tsx scripts/send-test-webhook.ts --prospect 4242 [--url http://localhost:3000]
 */
import { computeSignature } from '../src/lawmatics/signature.js';

function arg(name: string, fallback?: string): string {
  const index = process.argv.indexOf(`--${name}`);
  const value = index >= 0 ? process.argv[index + 1] : undefined;
  if (value === undefined && fallback === undefined) {
    throw new Error(`Missing required --${name}`);
  }
  return value ?? fallback!;
}

const secret = process.env.LAWMATICS_WEBHOOK_SECRET;
if (!secret) throw new Error('LAWMATICS_WEBHOOK_SECRET must be set');

const url = arg('url', 'http://localhost:3000') + '/webhooks/lawmatics';
const prospectId = arg('prospect');
const eventType = arg('event-type', 'matter_status_changed');
const timestamp = String(Math.floor(Date.now() / 1000));

const body = JSON.stringify({
  event_id: `evt_test_${Date.now()}`,
  firm_id: 'firm_test',
  event_type: eventType,
  version: '1',
  timestamp: Number(timestamp),
  data: { prospect_id: Number(prospectId), new_status: arg('status', 'Hired') },
});

const res = await fetch(url, {
  method: 'POST',
  headers: {
    'content-type': 'application/json',
    'x-lawmatics-signature': computeSignature(secret, timestamp, body),
    'x-lawmatics-timestamp': timestamp,
  },
  body,
});

console.log(`${res.status} ${res.statusText}`);
console.log(await res.text());
