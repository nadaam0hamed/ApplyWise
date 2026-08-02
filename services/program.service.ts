import type { Program } from '@/types/program';

/** Live Supabase has no `programs` table — returns an empty catalog. */
export const ProgramService = {
  async list(): Promise<Program[]> {
    return [];
  },

  async getById(_id: string): Promise<Program | null> {
    return null;
  },

  async findBySourceUrl(_url: string): Promise<Program | null> {
    return null;
  },

  async search(_query: string): Promise<Program[]> {
    return [];
  },
};
