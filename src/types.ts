export const INTENTS = [
  'interested',
  'meeting_request',
  'question',
  'objection',
  'not_interested',
  'unsubscribe',
  'referral',
  'wrong_person',
  'out_of_office',
  'auto_reply',
  'other',
] as const;

export type Intent = (typeof INTENTS)[number];

/** Your offer + voice. The agent uses this to decide what to actually say. */
export interface BusinessContext {
  companyName: string;
  senderName: string;
  senderTitle: string;
  /** One or two sentences describing what you sell and who it's for. */
  product: string;
  /** Concrete value props the agent may reference. */
  valueProps: string[];
  /** What a "win" looks like — usually booking a call. */
  callToAction: string;
  /** Scheduling link the agent offers to interested leads. */
  schedulingLink?: string;
  /** e.g. "warm, concise, no hype, lowercase-friendly". */
  tone: string;
  /** Claims the agent must never make (compliance / honesty guardrails). */
  doNotMakeClaims?: string[];
  /** Plain-text signature appended to every reply. */
  signature: string;
}

/** Normalized shape of an inbound reply, extracted from the webhook payload. */
export interface IncomingReply {
  /** The inbox that received the reply (Instantly "eaccount"). */
  eaccount: string;
  /** UUID of the message being replied to — needed to thread the response. */
  replyToUuid: string;
  leadEmail: string;
  leadName?: string;
  campaignId?: string;
  subject: string;
  /** Plain text of the prospect's latest reply. */
  body: string;
  /** Full thread text if the webhook provides it (improves draft quality). */
  threadText?: string;
  /** Original webhook payload, kept for debugging / field mapping. */
  raw: unknown;
}

/** Result of the single Claude call: detection + drafted reply together. */
export interface Analysis {
  intent: Intent;
  /** 0–1 confidence in the intent label. */
  confidence: number;
  /** How risky it would be to auto-send this reply unreviewed. */
  risk: 'low' | 'medium' | 'high';
  /** Short rationale, for the human reviewer. */
  reasoning: string;
  /** False for unsubscribes, out-of-office, auto-replies, wrong-person, etc. */
  shouldRespond: boolean;
  draftSubject: string;
  draftBody: string;
}

export type DraftStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'sent'
  | 'failed'
  | 'skipped';

export interface Draft {
  id: string;
  createdAt: string;
  updatedAt: string;
  status: DraftStatus;
  reply: IncomingReply;
  analysis: Analysis;
  /** The body actually sent (may be human-edited). */
  sentBody?: string;
  error?: string;
}
