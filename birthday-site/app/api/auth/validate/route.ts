import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

export async function POST(req: NextRequest) {
  const { code } = await req.json();
  if (!code || typeof code !== 'string') {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }

  const db = supabaseAdmin();
  const { data, error } = await db
    .from('guests')
    .select('code, name, active')
    .eq('code', code.trim().toUpperCase())
    .single();

  if (error || !data || !data.active) {
    return NextResponse.json(
      { error: "Hmm — that's not a code the Calf recognizes. Check with Ben." },
      { status: 401 }
    );
  }

  return NextResponse.json({ name: data.name, code: data.code });
}
