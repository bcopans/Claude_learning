import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

export async function GET() {
  const db = supabaseAdmin();
  const { data } = await db
    .from('costume_photos')
    .select('id, name, image_url, created_at')
    .order('created_at', { ascending: false });
  return NextResponse.json({ photos: data || [] });
}

export async function POST(req: NextRequest) {
  const { guest_code, name, image_url } = await req.json();

  if (!guest_code || !image_url) {
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

  const { error } = await db.from('costume_photos').insert({
    guest_code,
    name: name || guest.name,
    image_url,
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
