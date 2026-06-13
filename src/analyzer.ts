import Anthropic from '@anthropic-ai/sdk';
import { zodOutputFormat } from '@anthropic-ai/sdk/helpers/zod';
// The SDK's zod helper is built against zod v4; zod 3.25+ ships it at this
// subpath. Keep this in sync with the helper or types won't line up.
import { z } from 'zod/v4';
import { config } from './config.js';
import { INTENTS, type Analysis, type BusinessContext, type IncomingReply } from './types.js';

const client = new Anthropic({ apiKey: config.anthropic.apiKey });

// Structured output schema — guarantees the model returns exactly these fields.
const AnalysisSchema = z.object({
  intent: z.enum(INTENTS),
  confidence: z.number(),
  risk: z.enum(['low', 'medium', 'high']),
  reasoning: z.string(),
  shouldRespond: z.boolean(),
  draftSubject: z.string(),
  draftBody: z.string(),
});

function buildSystemPrompt(ctx: BusinessContext): string {
  return [
    `You are an SDR assistant handling replies to cold outreach for ${ctx.companyName}.`,
    `You reply on behalf of ${ctx.senderName} (${ctx.senderTitle}).`,
    ``,
    `WHAT WE SELL`,
    ctx.product,
    `Value props you may reference (only if relevant): ${ctx.valueProps.join('; ')}.`,
    `Primary goal: ${ctx.callToAction}.`,
    ctx.schedulingLink ? `Scheduling link to offer interested leads: ${ctx.schedulingLink}` : ``,
    ``,
    `YOUR JOB`,
    `1. Classify the prospect's reply into exactly one intent.`,
    `2. Decide whether a reply should be sent at all (shouldRespond).`,
    `3. Write the reply we should send — different every time, grounded in what`,
    `   they actually wrote. No templates, no filler, no "I hope this finds you well".`,
    ``,
    `INTENT HANDLING`,
    `- interested / meeting_request: be warm and specific; propose a concrete next`,
    `  step and share the scheduling link if available. Keep momentum.`,
    `- question: answer it directly and honestly, then nudge toward the next step.`,
    `- objection: acknowledge the concern genuinely, give a brief honest response,`,
    `  and offer a low-friction next step. Do not be pushy.`,
    `- referral: thank them, ask for the right person's contact warmly.`,
    `- not_interested: send a short, gracious break-up. No guilt-tripping. shouldRespond may be true.`,
    `- unsubscribe: shouldRespond=false. Do NOT reply; this must be honored by removing them.`,
    `- out_of_office / auto_reply: shouldRespond=false. Nothing to send.`,
    `- wrong_person: shouldRespond=false unless they point you to someone; then treat as referral.`,
    `- other: use judgment; default to a brief, human reply or shouldRespond=false if unclear.`,
    ``,
    `TONE: ${ctx.tone}. Match the prospect's energy and length. Be concise.`,
    ctx.doNotMakeClaims?.length
      ? `NEVER claim: ${ctx.doNotMakeClaims.join('; ')}.`
      : ``,
    ``,
    `DRAFT RULES`,
    `- draftBody is the email body only (no subject line inside it).`,
    `- End the body with this signature exactly:\n${ctx.signature}`,
    `- For draftSubject, reply in-thread: prefix the prospect's subject with "Re: "`,
    `  unless it already starts with "Re:".`,
    `- If shouldRespond is false, set draftBody to an empty string and draftSubject to "".`,
    `- risk = high if sending unreviewed could embarrass us (pricing claims,`,
    `  commitments, angry prospect); low for routine, safe replies.`,
  ]
    .filter(Boolean)
    .join('\n');
}

function buildUserPrompt(reply: IncomingReply): string {
  const lead = reply.leadName ? `${reply.leadName} <${reply.leadEmail}>` : reply.leadEmail;
  return [
    `A prospect replied to our cold email.`,
    ``,
    `From: ${lead}`,
    `Subject: ${reply.subject}`,
    ``,
    reply.threadText
      ? `FULL THREAD (oldest to newest):\n${reply.threadText}`
      : `THEIR REPLY:\n${reply.body}`,
    ``,
    `Analyze and draft our response.`,
  ].join('\n');
}

/**
 * Single Claude call: classifies the reply and drafts a contextual response.
 * Returns structured, validated output.
 */
export async function analyzeReply(
  reply: IncomingReply,
  ctx: BusinessContext,
): Promise<Analysis> {
  const response = await client.messages.parse({
    model: config.anthropic.model,
    max_tokens: 2000,
    system: buildSystemPrompt(ctx),
    messages: [{ role: 'user', content: buildUserPrompt(reply) }],
    output_config: { format: zodOutputFormat(AnalysisSchema) },
  });

  if (response.stop_reason === 'refusal') {
    throw new Error('Claude refused to analyze this reply.');
  }
  const parsed = response.parsed_output;
  if (!parsed) {
    throw new Error('Claude returned no parseable analysis.');
  }
  return parsed;
}
