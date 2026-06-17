import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

const ALLOWED = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif'];

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const file = formData.get('file') as File | null;
  const guestCode = formData.get('guest_code') as string | null;
  const guestName = formData.get('guest_name') as string | null;

  if (!file || !guestCode) {
    return NextResponse.json({ error: 'Missing file or guest_code' }, { status: 400 });
  }

  const ext = (file.name.split('.').pop() || 'jpg').toLowerCase();
  if (!ALLOWED.includes(ext)) {
    return NextResponse.json(
      { error: `File type .${ext} not supported. Use JPG, PNG, GIF, WebP, or HEIC.` },
      { status: 400 }
    );
  }

  const db = supabaseAdmin();
  const { data: guest } = await db
    .from('guests')
    .select('code, name')
    .eq('code', guestCode)
    .eq('active', true)
    .single();
  if (!guest) return NextResponse.json({ error: 'Invalid guest' }, { status: 401 });

  const path = `${guestCode}-${Date.now()}.${ext}`;
  const buffer = new Uint8Array(await file.arrayBuffer());

  const { error: uploadError } = await db.storage
    .from('costume-photos')
    .upload(path, buffer, { contentType: file.type || 'image/jpeg', upsert: false });

  if (uploadError) return NextResponse.json({ error: uploadError.message }, { status: 500 });

  const { data: urlData } = db.storage.from('costume-photos').getPublicUrl(path);

  // Save record to DB
  await db.from('costume_photos').insert({
    guest_code: guestCode,
    name: guestName || guest.name,
    image_url: urlData.publicUrl,
  });

  return NextResponse.json({ image_url: urlData.publicUrl });
}
