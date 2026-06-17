import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

function checkAdmin(req: NextRequest) {
  const auth = req.headers.get('x-admin-password');
  return auth === process.env.ADMIN_PASSWORD;
}

export async function GET(req: NextRequest) {
  if (!checkAdmin(req)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const db = supabaseAdmin();
  const { data } = await db
    .from('guests')
    .select('code, name, active, created_at')
    .order('created_at', { ascending: false });

  return NextResponse.json({ guests: data || [] });
}

export async function POST(req: NextRequest) {
  if (!checkAdmin(req)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { name, code } = await req.json();
  if (!name) return NextResponse.json({ error: 'Name required' }, { status: 400 });

  const generatedCode = code?.trim().toUpperCase() ||
    `BEN-${name.trim().toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12)}`;

  const db = supabaseAdmin();
  const { data, error } = await db
    .from('guests')
    .insert({ code: generatedCode, name: name.trim(), active: true })
    .select()
    .single();

  if (error) {
    if (error.code === '23505') {
      return NextResponse.json({ error: `Code "${generatedCode}" already exists. Try a custom code.` }, { status: 409 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ guest: data });
}

export async function PATCH(req: NextRequest) {
  if (!checkAdmin(req)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { code, active } = await req.json();
  if (!code) return NextResponse.json({ error: 'Code required' }, { status: 400 });

  const db = supabaseAdmin();
  const { error } = await db
    .from('guests')
    .update({ active })
    .eq('code', code);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  if (!checkAdmin(req)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { code } = await req.json();
  if (!code) return NextResponse.json({ error: 'Code required' }, { status: 400 });

  const db = supabaseAdmin();
  const { error } = await db.from('guests').delete().eq('code', code);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
