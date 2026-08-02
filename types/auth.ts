export type AuthUser = {
  id: string;
  email: string;
  fullName: string | null;
};

export type AuthResult = {
  error: string | null;
};
