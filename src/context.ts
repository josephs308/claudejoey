import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import type { BusinessContext } from './types.js';

const PATH = process.env.BUSINESS_CONTEXT_PATH ?? join('context', 'business.json');

let cached: BusinessContext | null = null;

/**
 * Load the business context that tells the agent what to actually say.
 * Edit context/business.json to change voice, offer, and guardrails — no code
 * changes needed.
 */
export async function loadBusinessContext(): Promise<BusinessContext> {
  if (cached) return cached;
  try {
    cached = JSON.parse(await readFile(PATH, 'utf8')) as BusinessContext;
    return cached;
  } catch (err) {
    throw new Error(
      `Could not load business context at ${PATH}. Copy context/business.example.json ` +
        `to context/business.json and fill it in. (${(err as Error).message})`,
    );
  }
}
