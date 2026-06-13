import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { config } from './config.js';
import type { Analysis, Draft, DraftStatus, IncomingReply } from './types.js';

const FILE = join(config.dataDir, 'drafts.json');

// Single-process JSON store. Adequate for one worker; swap for SQLite/Postgres
// if you run multiple instances or need concurrent writers.
let drafts: Map<string, Draft> | null = null;

async function load(): Promise<Map<string, Draft>> {
  if (drafts) return drafts;
  await mkdir(config.dataDir, { recursive: true });
  try {
    const raw = await readFile(FILE, 'utf8');
    const arr = JSON.parse(raw) as Draft[];
    drafts = new Map(arr.map((d) => [d.id, d]));
  } catch {
    drafts = new Map();
  }
  return drafts;
}

async function persist(): Promise<void> {
  const map = await load();
  await writeFile(FILE, JSON.stringify([...map.values()], null, 2));
}

export async function createDraft(
  reply: IncomingReply,
  analysis: Analysis,
): Promise<Draft> {
  const map = await load();
  const now = new Date().toISOString();
  const draft: Draft = {
    id: randomUUID(),
    createdAt: now,
    updatedAt: now,
    // Replies we shouldn't answer are recorded as 'skipped', not queued.
    status: analysis.shouldRespond ? 'pending' : 'skipped',
    reply,
    analysis,
  };
  map.set(draft.id, draft);
  await persist();
  return draft;
}

export async function getDraft(id: string): Promise<Draft | undefined> {
  return (await load()).get(id);
}

export async function listDrafts(status?: DraftStatus): Promise<Draft[]> {
  const all = [...(await load()).values()].sort((a, b) =>
    b.createdAt.localeCompare(a.createdAt),
  );
  return status ? all.filter((d) => d.status === status) : all;
}

export async function updateDraft(
  id: string,
  patch: Partial<Pick<Draft, 'status' | 'sentBody' | 'error'>>,
): Promise<Draft | undefined> {
  const map = await load();
  const draft = map.get(id);
  if (!draft) return undefined;
  Object.assign(draft, patch, { updatedAt: new Date().toISOString() });
  await persist();
  return draft;
}
