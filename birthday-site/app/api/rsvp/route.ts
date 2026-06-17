import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

export async function POST(req: NextRequest) {
  const { guest_code, name, attending, hotel, dietary, notes } = await req.json();

  if (!guest_code || !attending) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
  }

  const db = supabaseAdmin();

  // Verify the guest code is valid
  const { data: guest } = await db
    .from('guests')
    .select('code, name')
    .eq('code', guest_code)
    .eq('active', true)
    .single();

  if (!guest) {
    return NextResponse.json({ error: 'Invalid guest code' }, { status: 401 });
  }

  // Upsert: one RSVP per guest
  const { error } = await db.from('rsvps').upsert(
    { guest_code, name: name || guest.name, attending, hotel, dietary, notes },
    { onConflict: 'guest_code' }
  );

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get('code');
  if (!code) return NextResponse.json({ rsvp: null });

  const db = supabaseAdmin();
  const { data } = await db
    .from('rsvps')
    .select('attending, hotel, dietary, notes')
    .eq('guest_code', code)
    .single();

  return NextResponse.json({ rsvp: data });
}
