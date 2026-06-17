import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

function checkAdmin(req: NextRequest) {
  const auth = req.headers.get('x-admin-password');
  return auth === process.env.ADMIN_PASSWORD;
}

export async function GET(req: NextRequest) {
  if (!checkAdmin(req)) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

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
