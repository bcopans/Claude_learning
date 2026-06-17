import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

async function checkAdmin(req: NextRequest): Promise<boolean> {
  const code = req.headers.get('x-guest-code');
  if (!code) return false;
  const db = supabaseAdmin();
  const { data } = await db
    .from('guests')
    .select('code')
    .eq('code', code)
    .eq('active', true)
    .eq('is_admin', true)
    .single();
  return !!data;
}

export async function GET(req: NextRequest) {
  if (!(await checkAdmin(req))) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const db = supabaseAdmin();
  const { data } = await db
    .from('guests')
    .select('code, name, active, is_admin, created_at')
    .order('created_at', { ascending: false });

  return NextResponse.json({ guests: data || [] });
}

export async function POST(req: NextRequest) {
  if (!(await checkAdmin(req))) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { name, code } = await req.json();
  if (!name) return NextResponse.json({ error: 'Name required' }, { status: 400 });

  const generatedCode = code?.trim().toUpperCase() ||
    `BEN-${name.trim().toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12)}`;

  const db = supabaseAdmin();
  const { data, error } = await db
    .from('guests')
    .insert({ code: generatedCode, name: name.trim(), active: true, is_admin: false })
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
  if (!(await checkAdmin(req))) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { code, active, name, is_admin } = await req.json();
  if (!code) return NextResponse.json({ error: 'Code required' }, { status: 400 });

  const updates: Record<string, unknown> = {};
  if (active !== undefined) updates.active = active;
  if (name !== undefined) updates.name = String(name).trim();
  if (is_admin !== undefined) updates.is_admin = is_admin;

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ error: 'Nothing to update' }, { status: 400 });
  }

  const db = supabaseAdmin();
  const { error } = await db.from('guests').update(updates).eq('code', code);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  if (!(await checkAdmin(req))) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { code } = await req.json();
  if (!code) return NextResponse.json({ error: 'Code required' }, { status: 400 });

  const db = supabaseAdmin();
  const { error } = await db.from('guests').delete().eq('code', code);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
