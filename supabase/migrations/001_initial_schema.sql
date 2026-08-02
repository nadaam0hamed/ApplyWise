-- ApplyWise initial schema

-- Profiles (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  email TEXT NOT NULL,
  phone TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Popular scholarship/admission programs
CREATE TABLE IF NOT EXISTS programs (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  icon TEXT,
  scholarship_name TEXT NOT NULL,
  deadline DATE,
  duration TEXT,
  language TEXT,
  eligibility TEXT,
  required_documents JSONB NOT NULL DEFAULT '[]',
  language_requirement TEXT,
  gpa_requirement TEXT,
  recommendation_letters INT DEFAULT 0,
  passport_requirement TEXT,
  source_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Applications
CREATE TABLE IF NOT EXISTS applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  application_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'in_progress',
  program_name TEXT,
  target_program TEXT,
  target_university TEXT,
  country TEXT,
  deadline DATE,
  duration TEXT,
  language TEXT,
  requirement_source TEXT,
  source_url TEXT,
  readiness_score INT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Requirements
CREATE TABLE IF NOT EXISTS requirements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  is_required BOOLEAN NOT NULL DEFAULT TRUE,
  is_fulfilled BOOLEAN NOT NULL DEFAULT FALSE,
  eligibility TEXT,
  language_requirement TEXT,
  gpa_requirement TEXT,
  recommendation_letters_count INT,
  passport_requirement TEXT,
  source_url TEXT,
  extracted_data JSONB,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size BIGINT NOT NULL,
  storage_path TEXT NOT NULL,
  document_type TEXT,
  status TEXT NOT NULL DEFAULT 'uploaded',
  ocr_text TEXT,
  metadata JSONB,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Analyses
CREATE TABLE IF NOT EXISTS analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  readiness_score INT,
  applicant_info JSONB,
  uploaded_documents JSONB,
  missing_documents JSONB,
  checklist JSONB,
  recommendations JSONB,
  raw_result JSONB,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Timeline events
CREATE TABLE IF NOT EXISTS timeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  event_date DATE NOT NULL,
  event_name TEXT NOT NULL,
  event_type TEXT NOT NULL DEFAULT 'milestone',
  description TEXT,
  is_completed BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chat conversations
CREATE TABLE IF NOT EXISTS chat_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
  title TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Contact form submissions
CREATE TABLE IF NOT EXISTS contact_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_application_id ON documents(application_id);
CREATE INDEX IF NOT EXISTS idx_requirements_application_id ON requirements(application_id);
CREATE INDEX IF NOT EXISTS idx_analyses_application_id ON analyses(application_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_application_id ON timeline_events(application_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_id ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages(conversation_id);

-- Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE timeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Programs and contact_messages are public read / insert
ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_messages ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Applications policies
CREATE POLICY "Users can view own applications" ON applications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own applications" ON applications FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own applications" ON applications FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own applications" ON applications FOR DELETE USING (auth.uid() = user_id);

-- Requirements policies (via application ownership)
CREATE POLICY "Users can view own requirements" ON requirements FOR SELECT
  USING (EXISTS (SELECT 1 FROM applications a WHERE a.id = application_id AND a.user_id = auth.uid()));
CREATE POLICY "Users can insert own requirements" ON requirements FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM applications a WHERE a.id = application_id AND a.user_id = auth.uid()));
CREATE POLICY "Users can update own requirements" ON requirements FOR UPDATE
  USING (EXISTS (SELECT 1 FROM applications a WHERE a.id = application_id AND a.user_id = auth.uid()));
CREATE POLICY "Users can delete own requirements" ON requirements FOR DELETE
  USING (EXISTS (SELECT 1 FROM applications a WHERE a.id = application_id AND a.user_id = auth.uid()));

-- Documents policies
CREATE POLICY "Users can view own documents" ON documents FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own documents" ON documents FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own documents" ON documents FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own documents" ON documents FOR DELETE USING (auth.uid() = user_id);

-- Analyses policies
CREATE POLICY "Users can view own analyses" ON analyses FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own analyses" ON analyses FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own analyses" ON analyses FOR UPDATE USING (auth.uid() = user_id);

-- Timeline policies
CREATE POLICY "Users can view own timeline" ON timeline_events FOR SELECT
  USING (EXISTS (SELECT 1 FROM applications a WHERE a.id = application_id AND a.user_id = auth.uid()));
CREATE POLICY "Users can insert own timeline" ON timeline_events FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM applications a WHERE a.id = application_id AND a.user_id = auth.uid()));
CREATE POLICY "Users can update own timeline" ON timeline_events FOR UPDATE
  USING (EXISTS (SELECT 1 FROM applications a WHERE a.id = application_id AND a.user_id = auth.uid()));

-- Chat policies
CREATE POLICY "Users can view own conversations" ON chat_conversations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own conversations" ON chat_conversations FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own conversations" ON chat_conversations FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own messages" ON chat_messages FOR SELECT
  USING (EXISTS (SELECT 1 FROM chat_conversations c WHERE c.id = conversation_id AND c.user_id = auth.uid()));
CREATE POLICY "Users can insert own messages" ON chat_messages FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM chat_conversations c WHERE c.id = conversation_id AND c.user_id = auth.uid()));

-- Public programs read
CREATE POLICY "Anyone can view programs" ON programs FOR SELECT USING (true);

-- Contact messages insert (anonymous)
CREATE POLICY "Anyone can submit contact messages" ON contact_messages FOR INSERT WITH CHECK (true);

-- Seed popular programs
INSERT INTO programs (id, name, country, icon, scholarship_name, deadline, duration, language, eligibility, required_documents, language_requirement, gpa_requirement, recommendation_letters, passport_requirement, source_url)
VALUES
  ('erasmus', 'Erasmus Mundus', 'Europe', '🌍', 'Erasmus Mundus Master''s Program', '2025-01-15', '24 Months', 'English', 'Bachelor''s degree with minimum 3.0 GPA, English proficiency', '["Passport","Academic Transcripts","English Proficiency Certificate","Statement of Purpose","Recommendation Letters"]', 'TOEFL 90 or IELTS 6.5', '3.0 or higher', 2, 'Valid passport (6 months minimum validity)', 'https://www.eacea.ec.europa.eu/scholarships/emjmd-catalogue_en'),
  ('daad', 'DAAD', 'Germany', '🇩🇪', 'DAAD Scholarship 2026', '2025-10-31', '24 Months', 'English/German', 'Bachelor''s degree, strong academic record', '["Passport","Academic Certificates","CV","Motivation Letter","Recommendation Letters"]', 'IELTS 6.5 or TestDaF 4', '3.0 or higher', 2, 'Valid international passport', 'https://www.daad.de/en/study-and-research-in-germany/scholarships/'),
  ('chevening', 'Chevening', 'United Kingdom', '🇬🇧', 'Chevening Scholarship 2026', '2025-11-05', '12 Months', 'English', 'Minimum 2 years work experience, Bachelor''s degree', '["Passport","Academic Transcripts","CV","Personal Statement","Recommendation Letters"]', 'IELTS 6.5 overall', '2:1 honours degree or equivalent', 2, 'Valid passport', 'https://www.chevening.org/apply/'),
  ('fulbright', 'Fulbright', 'United States', '🇺🇸', 'Fulbright Foreign Student Program', '2025-09-15', '12 Months', 'English', 'Bachelor''s degree, leadership potential', '["Passport","Academic Transcripts","Personal Statement","Recommendation Letters","TOEFL Score"]', 'TOEFL 80 minimum', 'Strong academic record', 3, 'Valid passport', 'https://foreign.fulbrightonline.org/'),
  ('others', 'Others', 'Global', '📚', 'General Scholarship Program', '2025-12-31', 'Varies', 'English', 'Varies by program', '["Passport","Academic Transcripts","Statement of Purpose","Recommendation Letters"]', 'Varies', 'Varies', 2, 'Valid passport', NULL)
ON CONFLICT (id) DO NOTHING;

-- Storage bucket for documents (run in Supabase dashboard if needed)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false);
