import { z } from 'zod';

/**
 * Lawmatics webhook envelope. Parsed leniently: `data` is kept as a passthrough
 * object because the shape varies per event type and Lawmatics adds fields
 * without a version bump. Only the envelope fields we route on are required.
 */
export const webhookEnvelopeSchema = z.object({
  event_id: z.string().min(1),
  firm_id: z.union([z.string(), z.number()]).optional(),
  event_type: z.string().min(1),
  version: z.union([z.string(), z.number()]).optional(),
  timestamp: z.union([z.string(), z.number()]).optional(),
  data: z.record(z.unknown()).default({}),
});

export type WebhookEnvelope = z.infer<typeof webhookEnvelopeSchema>;

/** A Lawmatics custom field value as it appears nested on a parent record. */
export const customFieldValueSchema = z
  .object({
    id: z.union([z.string(), z.number()]).optional(),
    name: z.string().optional(),
    field_type: z.string().optional(),
    value_string: z.string().nullable().optional(),
    value_text: z.string().nullable().optional(),
    value_int: z.number().nullable().optional(),
    value_float: z.number().nullable().optional(),
    value_boolean: z.boolean().nullable().optional(),
    value_date: z.string().nullable().optional(),
    value_datetime: z.string().nullable().optional(),
    value_time: z.string().nullable().optional(),
  })
  .passthrough();

export type CustomFieldValue = z.infer<typeof customFieldValueSchema>;

/**
 * Reads whichever `value_*` key is populated. Lawmatics keys the value by the
 * field's declared type, so we probe in a fixed order rather than trusting
 * `field_type`, which is absent on some nested payloads.
 */
export function readCustomFieldValue(field: CustomFieldValue): string | number | boolean | null {
  const candidates = [
    field.value_string,
    field.value_text,
    field.value_datetime,
    field.value_date,
    field.value_time,
    field.value_int,
    field.value_float,
    field.value_boolean,
  ];
  for (const value of candidates) {
    if (value !== null && value !== undefined && value !== '') return value;
  }
  return null;
}

const idish = z.union([z.string(), z.number()]);

export const contactSchema = z
  .object({
    id: idish.optional(),
    first_name: z.string().nullable().optional(),
    middle_name: z.string().nullable().optional(),
    last_name: z.string().nullable().optional(),
    email: z.string().nullable().optional(),
    phone: z.string().nullable().optional(),
    cell_phone: z.string().nullable().optional(),
    work_phone: z.string().nullable().optional(),
    address: z.string().nullable().optional(),
    address2: z.string().nullable().optional(),
    city: z.string().nullable().optional(),
    state: z.string().nullable().optional(),
    zip: z.string().nullable().optional(),
    country: z.string().nullable().optional(),
    date_of_birth: z.string().nullable().optional(),
    company_name: z.string().nullable().optional(),
  })
  .passthrough();

export type LawmaticsContact = z.infer<typeof contactSchema>;

/**
 * A Lawmatics "prospect" -- their internal name for a matter, covering every
 * lead and case whether PNC, hired, or lost.
 */
export const prospectSchema = z
  .object({
    id: idish,
    name: z.string().nullable().optional(),
    case_number: z.string().nullable().optional(),
    created_at: z.string().nullable().optional(),
    updated_at: z.string().nullable().optional(),
    converted_at: z.string().nullable().optional(),
    estimated_value: z.union([z.string(), z.number()]).nullable().optional(),
    contact: contactSchema.nullable().optional(),
    // Association shapes vary: sometimes an object, sometimes a bare id/name.
    status: z.union([z.object({ name: z.string().nullable().optional() }).passthrough(), z.string()]).nullable().optional(),
    sub_status: z.union([z.object({ name: z.string().nullable().optional() }).passthrough(), z.string()]).nullable().optional(),
    practice_area: z.union([z.object({ name: z.string().nullable().optional() }).passthrough(), z.string()]).nullable().optional(),
    source: z.union([z.object({ name: z.string().nullable().optional() }).passthrough(), z.string()]).nullable().optional(),
    assigned_to: z
      .union([
        z.object({ first_name: z.string().nullable().optional(), last_name: z.string().nullable().optional(), email: z.string().nullable().optional() }).passthrough(),
        z.string(),
      ])
      .nullable()
      .optional(),
    custom_fields: z.array(customFieldValueSchema).optional(),
  })
  .passthrough();

export type LawmaticsProspect = z.infer<typeof prospectSchema>;

/** Association values arrive as `{name}` objects or bare strings. */
export function associationName(value: unknown): string | null {
  if (typeof value === 'string') return value.trim() || null;
  if (value && typeof value === 'object' && 'name' in value) {
    const name = (value as { name?: unknown }).name;
    if (typeof name === 'string') return name.trim() || null;
  }
  return null;
}
