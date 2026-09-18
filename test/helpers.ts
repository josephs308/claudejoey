import { loadConfig, type Config } from '../src/config.js';
import type { LawmaticsProspect } from '../src/lawmatics/types.js';

export function testConfig(overrides: Record<string, string> = {}): Config {
  return loadConfig({
    NODE_ENV: 'test',
    LAWMATICS_WEBHOOK_SECRET: 'whsec_test_abc123',
    LAWMATICS_ACCESS_TOKEN: 'test-token',
    EVE_MODE: 'mock',
    LOG_LEVEL: 'error',
    ...overrides,
  } as NodeJS.ProcessEnv);
}

export function makeProspect(overrides: Partial<LawmaticsProspect> = {}): LawmaticsProspect {
  return {
    id: 4242,
    name: 'Rivera v. Cascade Freight',
    case_number: 'PI-2026-0188',
    created_at: '2026-08-01T14:02:00Z',
    converted_at: '2026-09-15T09:30:00Z',
    estimated_value: '$125,000.00',
    status: { name: 'Hired' },
    sub_status: null,
    practice_area: { name: 'Personal Injury' },
    source: { name: 'Google Ads' },
    assigned_to: { first_name: 'Dana', last_name: 'Whitfield', email: 'dana@firm.example' },
    contact: {
      id: 909,
      first_name: 'Marisol',
      last_name: 'Rivera',
      email: 'Marisol.Rivera@Example.com',
      cell_phone: '(415) 555-0142',
      phone: '415-555-0199',
      address: '1200 Sutter St',
      address2: 'Apt 4B',
      city: 'San Francisco',
      state: 'CA',
      zip: '94109',
      country: 'US',
      date_of_birth: '1988-03-14',
    },
    custom_fields: [
      { name: 'Incident Date', field_type: 'date', value_date: '2026-07-19' },
      { name: 'Policy Limit', field_type: 'int', value_int: 250000 },
      { name: 'Police Report Filed', field_type: 'boolean', value_boolean: true },
      { name: 'Empty Field', field_type: 'string', value_string: '' },
    ],
    ...overrides,
  } as LawmaticsProspect;
}
