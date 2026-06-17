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
  const [rsvps, stays, costumes, offerings] = await Promise.all([
    db.from('rsvps').select('*').order('created_at', { ascending: false }),
    db.from('stays').select('*').order('created_at', { ascending: false }),
    db.from('costume_photos').select('*').order('created_at', { ascending: false }),
    db.from('offerings').select('guest_name, offering_type').order('created_at', { ascending: false }),
  ]);

  return NextResponse.json({
    rsvps: rsvps.data || [],
    stays: stays.data || [],
    costumes: costumes.data || [],
    offerings: offerings.data || [],
  });
}
