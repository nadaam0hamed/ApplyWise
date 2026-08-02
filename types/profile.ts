export type Profile = {
  id: string;
  full_name: string | null;
  email: string;
  created_at: string;
};

export type ProfileInsert = {
  id: string;
  full_name: string;
  email: string;
  created_at: string;
};
