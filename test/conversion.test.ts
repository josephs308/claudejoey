import { describe, it, expect } from 'vitest';
import { decideConversion, extractProspectId, isConvertibleEvent } from '../src/pipeline/conversion.js';
import { webhookEnvelopeSchema } from '../src/lawmatics/types.js';
import { testConfig, makeProspect } from './helpers.js';

describe('isConvertibleEvent', () => {
  it('accepts matter status changes', () => {
    expect(isConvertibleEvent('matter_status_changed')).toBe(true);
    expect(isConvertibleEvent('MATTER_STATUS_CHANGED')).toBe(true);
  });

  it('ignores unrelated events', () => {
    expect(isConvertibleEvent('invoice_paid')).toBe(false);
    expect(isConvertibleEvent('document_signed')).toBe(false);
  });
});

describe('extractProspectId', () => {
  const envelope = (data: Record<string, unknown>) =>
    webhookEnvelopeSchema.parse({ event_id: 'evt_1', event_type: 'matter_status_changed', data });

  it.each([
    ['prospect_id', { prospect_id: 77 }],
    ['matter_id', { matter_id: '77' }],
    ['bare id', { id: 77 }],
    ['nested prospect', { prospect: { id: 77 } }],
    ['nested matter', { matter: { id: 77 } }],
  ])('reads the id from %s', (_label, data) => {
    expect(extractProspectId(envelope(data))).toBe('77');
  });

  it('returns null when no id is present', () => {
    expect(extractProspectId(envelope({ unrelated: true }))).toBeNull();
  });
});

describe('decideConversion', () => {
  const cfg = testConfig();

  it('syncs a matter whose status is a configured conversion status', () => {
    expect(decideConversion(makeProspect(), cfg)).toEqual({
      sync: true,
      status: 'Hired',
      prospectId: '4242',
    });
  });

  it('matches status case-insensitively', () => {
    const result = decideConversion(makeProspect({ status: { name: 'RETAINED' } }), cfg);
    expect(result.sync).toBe(true);
  });

  it('accepts a bare string status', () => {
    expect(decideConversion(makeProspect({ status: 'signed' }), cfg).sync).toBe(true);
  });

  it('skips a lead that has not converted', () => {
    expect(decideConversion(makeProspect({ status: { name: 'New Lead' } }), cfg)).toEqual({
      sync: false,
      reason: 'status_not_a_conversion:new lead',
    });
  });

  it('skips a lost matter', () => {
    expect(decideConversion(makeProspect({ status: { name: 'Lost' } }), cfg).sync).toBe(false);
  });

  it('skips a matter with no status at all', () => {
    expect(decideConversion(makeProspect({ status: null }), cfg)).toEqual({
      sync: false,
      reason: 'prospect_has_no_status',
    });
  });

  it('honours the excluded sub-status list', () => {
    const cfgWithExclusion = testConfig({ CONVERSION_EXCLUDED_SUBSTATUSES: 'pending conflict check' });
    const prospect = makeProspect({ sub_status: { name: 'Pending Conflict Check' } });
    expect(decideConversion(prospect, cfgWithExclusion)).toEqual({
      sync: false,
      reason: 'sub_status_excluded:pending conflict check',
    });
  });

  it('respects a firm-specific status list', () => {
    const cfgCustom = testConfig({ CONVERSION_STATUSES: 'engaged' });
    expect(decideConversion(makeProspect({ status: { name: 'Hired' } }), cfgCustom).sync).toBe(false);
    expect(decideConversion(makeProspect({ status: { name: 'Engaged' } }), cfgCustom).sync).toBe(true);
  });
});
