import { NextRequest, NextResponse } from 'next/server';import { supabaseAdmin } from '@/lib/supabase';

export async function GET() {
  const db = supabaseAdmin();
  const { count } = await db
    .from('offerings')
    .select('*', { count: 'exact', head: true });

  const { data } = await db
    .from('offerings')
    .select('id, guest_name, offering_type, x_position, y_position, rotation, scale, created_at')
    .order('created_at', { ascending: true })
    .limit(200);

  return NextResponse.json({ offerings: data || [], total: count || 0 });
}

export async function POST(req: NextRequest) {
  const { guest_code, guest_name, offering_type, x_position, y_position, rotation, scale } =
    await req.json();

  if (!guest_code || !offering_type) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
  }

  const db = supabaseAdmin();

  const { data: guest } = await db
    .from('guests')
    .select('code')
    .eq('code', guest_code)
    .eq('active', true)
    .single();

  if (!guest) {
    return NextResponse.json({ error: 'Invalid guest code' }, { status: 401 });
  }

  const { data, error } = await db
    .from('offerings')
    .insert({ guest_code, guest_name, offering_type, x_position, y_position, rotation, scale })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ offering: data });
}

export async function DELETE(req: NextRequest) {
  const db = supabaseAdmin();

  // Verify caller is an admin guest
  const code = req.headers.get('x-guest-code');
  if (!code) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { data: admin } = await db
    .from('guests')
    .select('code')
    .eq('code', code)
    .eq('active', true)
    .eq('is_admin', true)
    .single();
  if (!admin) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { error } = await db.from('offerings').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
