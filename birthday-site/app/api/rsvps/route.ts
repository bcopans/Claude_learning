import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

export async function GET() {
  const db = supabaseAdmin();
  const { data } = await db
    .from('rsvps')
    .select('guest_code, name, attending, hotel')
    .eq('attending', 'yes')
    .order('created_at', { ascending: true });
  return NextResponse.json({ rsvps: data || [] });
}
