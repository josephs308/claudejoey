import {
  associationName,
  readCustomFieldValue,
  type LawmaticsProspect,
} from '../lawmatics/types.js';

/**
 * Canonical client record: the vendor-neutral shape that sits between Lawmatics
 * and Eve. Both sides map to and from this, so a change to either vendor's
 * payload touches exactly one adapter.
 */
export interface CanonicalClient {
  /** Stable key used for idempotency on both sides. */
  sourceSystem: 'lawmatics';
  sourceProspectId: string;
  sourceContactId: string | null;

  firstName: string | null;
  middleName: string | null;
  lastName: string | null;
  fullName: string;
  email: string | null;
  phones: { type: 'mobile' | 'home' | 'work'; number: string }[];
  dateOfBirth: string | null;

  address: {
    line1: string | null;
    line2: string | null;
    city: string | null;
    state: string | null;
    postalCode: string | null;
    country: string | null;
  };

  matter: {
    name: string | null;
    caseNumber: string | null;
    practiceArea: string | null;
    status: string | null;
    subStatus: string | null;
    source: string | null;
    estimatedValue: number | null;
    openedAt: string | null;
    convertedAt: string | null;
    assignedTo: { name: string | null; email: string | null } | null;
  };

  /** Lawmatics custom fields, keyed by field name. */
  customFields: Record<string, string | number | boolean>;
}

function clean(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
}

/** E.164-ish normalisation: keeps digits, assumes +1 for 10-digit US numbers. */
export function normalisePhone(raw: unknown): string | null {
  const value = clean(raw);
  if (!value) return null;
  const hasPlus = value.trim().startsWith('+');
  const digits = value.replace(/\D/g, '');
  if (digits.length === 0) return null;
  if (hasPlus) return `+${digits}`;
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  return digits;
}

function toNumber(value: unknown): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value === 'string') {
    // Strip currency formatting: "$12,500.00" -> 12500
    const parsed = Number(value.replace(/[^0-9.-]/g, ''));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function toCanonicalClient(prospect: LawmaticsProspect): CanonicalClient {
  const contact = prospect.contact ?? {};

  const firstName = clean(contact.first_name);
  const middleName = clean(contact.middle_name);
  const lastName = clean(contact.last_name);
  const fullName =
    [firstName, middleName, lastName].filter(Boolean).join(' ') ||
    clean(contact.company_name) ||
    clean(prospect.name) ||
    `Lawmatics matter ${prospect.id}`;

  const phones: CanonicalClient['phones'] = [];
  const seen = new Set<string>();
  for (const [type, raw] of [
    ['mobile', contact.cell_phone],
    ['home', contact.phone],
    ['work', contact.work_phone],
  ] as const) {
    const number = normalisePhone(raw);
    if (number && !seen.has(number)) {
      seen.add(number);
      phones.push({ type, number });
    }
  }

  const customFields: Record<string, string | number | boolean> = {};
  for (const field of prospect.custom_fields ?? []) {
    const name = clean(field.name);
    if (!name) continue;
    const value = readCustomFieldValue(field);
    if (value !== null) customFields[name] = value;
  }

  const assignee = prospect.assigned_to;
  const assignedTo =
    assignee && typeof assignee === 'object'
      ? {
          name:
            [clean(assignee.first_name), clean(assignee.last_name)].filter(Boolean).join(' ') || null,
          email: clean(assignee.email),
        }
      : typeof assignee === 'string'
        ? { name: clean(assignee), email: null }
        : null;

  return {
    sourceSystem: 'lawmatics',
    sourceProspectId: String(prospect.id),
    sourceContactId: contact.id !== undefined && contact.id !== null ? String(contact.id) : null,
    firstName,
    middleName,
    lastName,
    fullName,
    email: clean(contact.email)?.toLowerCase() ?? null,
    phones,
    dateOfBirth: clean(contact.date_of_birth),
    address: {
      line1: clean(contact.address),
      line2: clean(contact.address2),
      city: clean(contact.city),
      state: clean(contact.state),
      postalCode: clean(contact.zip),
      country: clean(contact.country),
    },
    matter: {
      name: clean(prospect.name),
      caseNumber: clean(prospect.case_number),
      practiceArea: associationName(prospect.practice_area),
      status: associationName(prospect.status),
      subStatus: associationName(prospect.sub_status),
      source: associationName(prospect.source),
      estimatedValue: toNumber(prospect.estimated_value),
      openedAt: clean(prospect.created_at),
      convertedAt: clean(prospect.converted_at),
      assignedTo,
    },
    customFields,
  };
}
