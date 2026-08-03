import { type NextRequest, NextResponse } from 'next/server';

import { updateSession } from '@/lib/supabase/middleware';

export async function middleware(request: NextRequest) {
  try {
    return updateSession(request);
  } catch (error) {
    // If Supabase env vars are missing, skip middleware (build time)
    return NextResponse.next();
  }
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/applications/:path*',
    '/login',
    '/signup',
    '/auth/login',
    '/auth/register',
  ],
};
