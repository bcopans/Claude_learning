import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

export async function GET() {
  const db = supabaseAdmin();
  const { data } = await db
    .from('stays')
    .select('id, guest_code, name, hotel, arrive, depart, created_at')
    .order('created_at', { ascending: true });
  return NextResponse.json({ stays: data || [] });
}

export async function POST(req: NextRequest) {
  const { guest_code, name, hotel, arrive, depart } = await req.json();

  if (!guest_code || !hotel) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
  }

  const db = supabaseAdmin();
  const { data: guest } = await db
    .from('guests')
    .select('code, name')
    .eq('code', guest_code)
    .eq('active', true)
    .single();

  if (!guest) return NextResponse.json({ error: 'Invalid guest' }, { status: 401 });

  const { error } = await db.from('stays').upsert(
    { guest_code, name: name || guest.name, hotel, arrive, depart },
    { onConflict: 'guest_code' }
  );

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  const { guest_code } = await req.json();
  if (!guest_code) return NextResponse.json({ error: 'Missing guest_code' }, { status: 400 });

  const db = supabaseAdmin();
  const { data: guest } = await db
    .from('guests').select('code').eq('code', guest_code).eq('active', true).single();
  if (!guest) return NextResponse.json({ error: 'Invalid guest' }, { status: 401 });

  const { error } = await db.from('stays').delete().eq('guest_code', guest_code);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
