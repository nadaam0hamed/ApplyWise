/** UI catalog entry — not stored in Supabase (no `programs` table in live DB). */
export interface Program {
  id: string;
  name: string;
  country: string;
  icon: string | null;
  scholarship_name: string;
  deadline: string | null;
  duration: string | null;
  language: string | null;
  eligibility: string | null;
  required_documents: string[];
  language_requirement: string | null;
  gpa_requirement: string | null;
  recommendation_letters: number;
  passport_requirement: string | null;
  source_url: string | null;
  created_at: string;
}
