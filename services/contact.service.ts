export interface ContactMessageInsert {
  name: string;
  email: string;
  message: string;
}

/** Live Supabase has no `contact_messages` table. */
export const ContactService = {
  async submit(_payload: ContactMessageInsert): Promise<void> {
    throw new Error(
      'Contact form submissions are not available — the contact_messages table does not exist in the live database.',
    );
  },
};
