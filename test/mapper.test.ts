import { describe, it, expect } from 'vitest';
import { toCanonicalClient, normalisePhone } from '../src/pipeline/mapper.js';
import { buildEvePayload } from '../src/eve/client.js';
import { makeProspect, testConfig } from './helpers.js';

describe('normalisePhone', () => {
  it.each([
    ['(415) 555-0142', '+14155550142'],
    ['415-555-0142', '+14155550142'],
    ['14155550142', '+14155550142'],
    ['+44 20 7946 0958', '+442079460958'],
  ])('normalises %s', (input, expected) => {
    expect(normalisePhone(input)).toBe(expected);
  });

  it.each([null, undefined, '', '   ', 'n/a'])('returns null for %s', (input) => {
    expect(normalisePhone(input)).toBeNull();
  });
});

describe('toCanonicalClient', () => {
  it('maps a converted matter into the canonical shape', () => {
    const client = toCanonicalClient(makeProspect());

    expect(client.sourceProspectId).toBe('4242');
    expect(client.sourceContactId).toBe('909');
    expect(client.fullName).toBe('Marisol Rivera');
    expect(client.email).toBe('marisol.rivera@example.com'); // lower-cased
    expect(client.dateOfBirth).toBe('1988-03-14');
    expect(client.address).toEqual({
      line1: '1200 Sutter St',
      line2: 'Apt 4B',
      city: 'San Francisco',
      state: 'CA',
      postalCode: '94109',
      country: 'US',
    });
    expect(client.matter.practiceArea).toBe('Personal Injury');
    expect(client.matter.caseNumber).toBe('PI-2026-0188');
    expect(client.matter.assignedTo).toEqual({ name: 'Dana Whitfield', email: 'dana@firm.example' });
  });

  it('parses a currency-formatted estimated value', () => {
    expect(toCanonicalClient(makeProspect()).matter.estimatedValue).toBe(125000);
  });

  it('collects and de-duplicates phone numbers by type', () => {
    const client = toCanonicalClient(makeProspect());
    expect(client.phones).toEqual([
      { type: 'mobile', number: '+14155550142' },
      { type: 'home', number: '+14155550199' },
    ]);
  });

  it('does not repeat a number listed under two fields', () => {
    const prospect = makeProspect();
    prospect.contact!.phone = '(415) 555-0142'; // same as cell
    const client = toCanonicalClient(prospect);
    expect(client.phones).toEqual([{ type: 'mobile', number: '+14155550142' }]);
  });

  it('flattens custom fields by name, dropping empty values', () => {
    const client = toCanonicalClient(makeProspect());
    expect(client.customFields).toEqual({
      'Incident Date': '2026-07-19',
      'Policy Limit': 250000,
      'Police Report Filed': true,
    });
    expect(client.customFields).not.toHaveProperty('Empty Field');
  });

  it('falls back to the company name for an organisation client', () => {
    const prospect = makeProspect();
    prospect.contact = { id: 12, company_name: 'Cascade Freight LLC' };
    expect(toCanonicalClient(prospect).fullName).toBe('Cascade Freight LLC');
  });

  it('falls back to the matter name when the contact has no name', () => {
    const prospect = makeProspect();
    prospect.contact = { id: 12 };
    expect(toCanonicalClient(prospect).fullName).toBe('Rivera v. Cascade Freight');
  });

  it('never produces an empty name', () => {
    const prospect = makeProspect({ name: null });
    prospect.contact = {};
    expect(toCanonicalClient(prospect).fullName).toBe('Lawmatics matter 4242');
  });

  it('survives a prospect with no contact at all', () => {
    const prospect = makeProspect({ contact: null });
    const client = toCanonicalClient(prospect);
    expect(client.email).toBeNull();
    expect(client.phones).toEqual([]);
    expect(client.sourceContactId).toBeNull();
  });

  it('treats whitespace-only strings as absent', () => {
    const prospect = makeProspect();
    prospect.contact!.city = '   ';
    expect(toCanonicalClient(prospect).address.city).toBeNull();
  });
});

describe('buildEvePayload', () => {
  it('carries a stable external id for idempotency', () => {
    const payload = buildEvePayload(toCanonicalClient(makeProspect()), testConfig());
    expect(payload.external_id).toBe('lawmatics:4242');
    expect(payload.source).toBe('lawmatics');
  });

  it('includes the firm id only when configured', () => {
    const client = toCanonicalClient(makeProspect());
    expect(buildEvePayload(client, testConfig())).not.toHaveProperty('firm_id');
    expect(buildEvePayload(client, testConfig({ EVE_FIRM_ID: 'firm_99' })).firm_id).toBe('firm_99');
  });

  it('preserves lawmatics custom fields in metadata', () => {
    const payload = buildEvePayload(toCanonicalClient(makeProspect()), testConfig());
    expect(payload.metadata).toMatchObject({
      lawmatics_prospect_id: '4242',
      custom_fields: { 'Policy Limit': 250000 },
    });
  });
});
