'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout, { SessionWithRsvp } from '@/components/ProtectedLayout';
import { C } from '@/lib/constants';
import { supabase } from '@/lib/supabase';

export default function MembersPage() {
  return (
    <ProtectedLayout>
      {(session) => <MembersContent session={session} />}
    </ProtectedLayout>
  );
}

const FONT = "'Space Grotesk', system-ui, sans-serif";

interface Stay {
  id: string;
  name: string;
  hotel: string;
  arrive: string | null;
  depart: string | null;
}

interface Photo {
  id: string;
  name: string;
  image_url: string;
}

function MembersContent({ session }: { session: SessionWithRsvp }) {
  const router = useRouter();
  const [tab, setTab] = useState<'stays' | 'costumes'>('stays');

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  if (!session.rsvped) {
    return (
      <div style={{ background: C.green, minHeight: 'calc(100vh - 49px)', padding: '40px 20px' }}>
        <div style={{ maxWidth: 760, margin: '0 auto', textAlign: 'center', paddingTop: 40 }}>
          <div style={{ fontSize: 54, marginBottom: 14 }}>🔒</div>
          <h1
            style={{
              fontFamily: "'Archivo Black', sans-serif",
              fontSize: 'clamp(26px,5vw,38px)',
              lineHeight: 1,
              textTransform: 'uppercase',
              color: C.cream,
              margin: '0 0 20px',
            }}
          >
            Members only
          </h1>
          <p
            style={{
              fontSize: 16,
              color: C.mint,
              maxWidth: 380,
              margin: '0 auto 22px',
              lineHeight: 1.6,
            }}
          >
            Who's staying where and the costume wall unlock once you RSVP yes.
          </p>
          <button
            onClick={() => {
              router.push('/explore?section=rsvp');
            }}
            style={{
              background: C.coral,
              color: C.greenDeep,
              border: 'none',
              borderRadius: 99,
              fontFamily: FONT,
              fontWeight: 700,
              fontSize: 14,
              padding: '13px 30px',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              cursor: 'pointer',
            }}
          >
            Go RSVP →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: C.green, minHeight: 'calc(100vh - 49px)', padding: '40px 20px 60px' }}>
      <div style={{ maxWidth: 760, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: C.mango,
              marginBottom: 14,
            }}
          >
            Members only · welcome, {session.name}
          </div>
          <h1
            style={{
              fontFamily: "'Archivo Black', sans-serif",
              fontSize: 'clamp(26px,5vw,38px)',
              lineHeight: 1,
              textTransform: 'uppercase',
              color: C.cream,
              margin: 0,
            }}
          >
            The Inner Sanctum
          </h1>
        </div>

        <div
          style={{
            display: 'flex',
            gap: 8,
            flexWrap: 'wrap',
            justifyContent: 'center',
            marginBottom: 24,
          }}
        >
          {(
            [
              ['stays', '🏨 Who\'s Where'],
              ['costumes', '📸 Costume Wall'],
            ] as [string, string][]
          ).map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id as 'stays' | 'costumes')}
              style={{
                padding: '9px 16px',
                borderRadius: 99,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 700,
                fontFamily: FONT,
                border: tab === id ? `1.5px solid ${C.mango}` : '0.5px solid rgba(255,248,231,0.25)',
                background: tab === id ? C.mango : 'transparent',
                color: tab === id ? C.greenDeep : C.cream,
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === 'stays' && <StaysTab session={session} />}
        {tab === 'costumes' && <CostumeWallTab session={session} />}
      </div>
    </div>
  );
}

function StaysTab({ session }: { session: SessionWithRsvp }) {
  const [stays, setStays] = useState<Stay[]>([]);
  const [hotel, setHotel] = useState('');
  const [arrive, setArrive] = useState('');
  const [depart, setDepart] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/stays')
      .then((r) => r.json())
      .then(({ stays }) => setStays(stays || []))
      .catch(() => {})
      .finally(() => setLoading(false));

    // Pre-fill with guest's existing stay
    const myStay = stays.find((s) => s.name === session.name);
    if (myStay) {
      setHotel(myStay.hotel);
      setArrive(myStay.arrive || '');
      setDepart(myStay.depart || '');
    }
  }, [session.name]);

  const save = async () => {
    if (!hotel) return;
    setSaving(true);
    try {
      const res = await fetch('/api/stays', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guest_code: session.code,
          name: session.name,
          hotel,
          arrive: arrive || null,
          depart: depart || null,
        }),
      });
      if (res.ok) {
        const r = await fetch('/api/stays');
        const d = await r.json();
        setStays(d.stays || []);
      }
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const fmt = (d: string | null) =>
    d ? new Date(d + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—';

  const card: React.CSSProperties = {
    background: 'rgba(255,248,231,0.07)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
  };

  const dateInput: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: 8,
    border: '0.5px solid #1d6b54',
    background: 'rgba(255,248,231,0.06)',
    color: C.cream,
    fontSize: 16,
    fontFamily: FONT,
    boxSizing: 'border-box',
    colorScheme: 'dark' as 'dark',
  };

  return (
    <div style={{ maxWidth: 560, margin: '0 auto' }}>
      <div style={card}>
        <div style={{ fontSize: 14, fontWeight: 700, color: C.cream, marginBottom: 10 }}>
          Where are you staying?
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          {['Fasano', 'Arpoador', 'Other / Airbnb', 'Undecided'].map((h) => (
            <button
              key={h}
              onClick={() => setHotel(h)}
              style={{
                padding: '8px 12px',
                borderRadius: 99,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 700,
                fontFamily: FONT,
                border: hotel === h ? `1.5px solid ${C.mango}` : '0.5px solid rgba(255,248,231,0.25)',
                background: hotel === h ? C.mango : 'transparent',
                color: hotel === h ? C.greenDeep : C.cream,
              }}
            >
              {h}
            </button>
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
          <div>
            <label style={{ fontSize: 12, color: C.mint, display: 'block', marginBottom: 4 }}>
              Arrive
            </label>
            <input
              type="date"
              value={arrive}
              min="2027-01-28"
              max="2027-02-20"
              onChange={(e) => setArrive(e.target.value)}
              style={dateInput}
            />
          </div>
          <div>
            <label style={{ fontSize: 12, color: C.mint, display: 'block', marginBottom: 4 }}>
              Depart
            </label>
            <input
              type="date"
              value={depart}
              min="2027-01-28"
              max="2027-02-20"
              onChange={(e) => setDepart(e.target.value)}
              style={dateInput}
            />
          </div>
        </div>
        <button
          onClick={save}
          disabled={saving || !hotel}
          style={{
            background: saving ? '#a04040' : C.coral,
            color: C.greenDeep,
            border: 'none',
            borderRadius: 8,
            padding: '10px 20px',
            fontWeight: 700,
            fontSize: 13,
            cursor: saving ? 'not-allowed' : 'pointer',
            fontFamily: FONT,
          }}
        >
          {saving ? 'Saving…' : 'Post my stay'}
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: C.mint, fontSize: 13 }}>Loading…</div>
      ) : stays.length === 0 ? (
        <div style={{ textAlign: 'center', color: C.mint, fontSize: 13, marginTop: 16 }}>
          No one's posted yet — be the first.
        </div>
      ) : (
        stays.map((s) => (
          <div key={s.id} style={card}>
            <strong style={{ color: C.cream }}>{s.name}</strong>{' '}
            <span style={{ color: C.mango, fontWeight: 700 }}>· {s.hotel}</span>
            <div style={{ fontSize: 13, color: C.mint, marginTop: 4 }}>
              📅 {fmt(s.arrive)} → {fmt(s.depart)}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function CostumeWallTab({ session }: { session: SessionWithRsvp }) {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/costumes')
      .then((r) => r.json())
      .then(({ photos }) => setPhotos(photos || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const onPick = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const ext = file.name.split('.').pop() || 'jpg';
      const path = `costumes/${session.code}-${Date.now()}.${ext}`;
      const { error: uploadError } = await supabase.storage
        .from('costume-photos')
        .upload(path, file, { upsert: false });

      if (uploadError) throw uploadError;

      const { data: urlData } = supabase.storage.from('costume-photos').getPublicUrl(path);

      await fetch('/api/costumes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guest_code: session.code,
          name: session.name,
          image_url: urlData.publicUrl,
        }),
      });

      const r = await fetch('/api/costumes');
      const d = await r.json();
      setPhotos(d.photos || []);
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 18 }}>
        <label
          style={{
            display: 'inline-block',
            background: uploading ? '#a04040' : C.coral,
            color: C.greenDeep,
            borderRadius: 99,
            padding: '12px 26px',
            fontWeight: 700,
            fontSize: 14,
            cursor: uploading ? 'not-allowed' : 'pointer',
            fontFamily: FONT,
          }}
        >
          {uploading ? 'Uploading…' : '📸 Upload your look'}
          <input
            type="file"
            accept="image/*"
            onChange={onPick}
            style={{ display: 'none' }}
            disabled={uploading}
          />
        </label>
        <div style={{ fontSize: 12, color: C.mint, marginTop: 8 }}>
          Birds, gods, or cowboys — show the group your costumes.
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: C.mint, fontSize: 13 }}>Loading…</div>
      ) : photos.length === 0 ? (
        <div style={{ textAlign: 'center', color: C.mint, fontSize: 13, marginTop: 16 }}>
          No looks posted yet. Set the standard. 🪶
        </div>
      ) : (
        <div
          style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px,1fr))', gap: 10 }}
        >
          {photos.map((p) => (
            <div
              key={p.id}
              style={{
                borderRadius: 12,
                overflow: 'hidden',
                border: '0.5px solid rgba(255,248,231,0.2)',
              }}
            >
              <img
                src={p.image_url}
                alt="costume"
                style={{ width: '100%', height: 160, objectFit: 'cover', display: 'block' }}
              />
              <div
                style={{
                  fontSize: 12,
                  color: C.cream,
                  padding: '6px 8px',
                  background: 'rgba(255,248,231,0.07)',
                }}
              >
                {p.name}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
