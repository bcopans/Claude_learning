'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout, { SessionWithRsvp } from '@/components/ProtectedLayout';
import { C } from '@/lib/constants';

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
  guest_code: string;
  name: string;
  hotel: string;
  arrive: string | null;
  depart: string | null;
}

interface Rsvp {
  guest_code: string;
  name: string;
  attending: string;
  hotel: string;
}

interface Photo {
  id: string;
  guest_code: string;
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
            onClick={() => router.push('/explore?section=rsvp')}
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
              ['stays', "🏨 Who's Where"],
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
  const [rsvps, setRsvps] = useState<Rsvp[]>([]);
  const [hotel, setHotel] = useState('Undecided');
  const [arrive, setArrive] = useState('');
  const [depart, setDepart] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [hasPosted, setHasPosted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/stays').then((r) => r.json()),
      fetch('/api/rsvps').then((r) => r.json()),
    ])
      .then(([stayData, rsvpData]) => {
        const loadedStays: Stay[] = stayData.stays || [];
        const loadedRsvps: Rsvp[] = rsvpData.rsvps || [];
        setStays(loadedStays);
        setRsvps(loadedRsvps);

        const myStay = loadedStays.find((s) => s.guest_code === session.code);
        if (myStay) {
          setHotel(myStay.hotel);
          setArrive(myStay.arrive || '');
          setDepart(myStay.depart || '');
          setHasPosted(true);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [session.code]);

  const refreshStays = async () => {
    const r = await fetch('/api/stays');
    const d = await r.json();
    setStays(d.stays || []);
  };

  const save = async () => {
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
        await refreshStays();
        setHasPosted(true);
      }
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const deleteStay = async () => {
    setDeleting(true);
    try {
      const res = await fetch('/api/stays', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_code: session.code }),
      });
      if (res.ok) {
        await refreshStays();
        setHasPosted(false);
        setHotel('Undecided');
        setArrive('');
        setDepart('');
      }
    } catch {
    } finally {
      setDeleting(false);
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

  // Merge RSVPs with stays: everyone who said yes gets a row
  const attendees = rsvps.map((r) => {
    const stay = stays.find((s) => s.guest_code === r.guest_code);
    return { ...r, stay: stay || null };
  });

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
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={save}
            disabled={saving}
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
            {saving ? 'Saving…' : hasPosted ? 'Update my stay' : 'Post my stay'}
          </button>
          {hasPosted && (
            <button
              onClick={deleteStay}
              disabled={deleting}
              style={{
                background: 'none',
                color: 'rgba(255,248,231,0.5)',
                border: '0.5px solid rgba(255,248,231,0.25)',
                borderRadius: 8,
                padding: '10px 16px',
                fontWeight: 600,
                fontSize: 13,
                cursor: deleting ? 'not-allowed' : 'pointer',
                fontFamily: FONT,
              }}
            >
              {deleting ? 'Deleting…' : 'Delete my stay'}
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: C.mint, fontSize: 13 }}>Loading…</div>
      ) : attendees.length === 0 ? (
        <div style={{ textAlign: 'center', color: C.mint, fontSize: 13, marginTop: 16 }}>
          No one's RSVPd yet.
        </div>
      ) : (
        <>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: C.mango,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 8,
            }}
          >
            Who's coming ({attendees.length})
          </div>
          {attendees.map((a) => (
            <div key={a.guest_code} style={card}>
              <strong style={{ color: C.cream }}>{a.name}</strong>
              {a.stay ? (
                <>
                  {' '}
                  <span style={{ color: C.mango, fontWeight: 700 }}>· {a.stay.hotel}</span>
                  <div style={{ fontSize: 13, color: C.mint, marginTop: 4 }}>
                    📅 {fmt(a.stay.arrive)} → {fmt(a.stay.depart)}
                  </div>
                </>
              ) : (
                <span style={{ fontSize: 13, color: 'rgba(255,248,231,0.35)', marginLeft: 6 }}>
                  · stay TBD
                </span>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function CostumeWallTab({ session }: { session: SessionWithRsvp }) {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch('/api/costumes')
      .then((r) => r.json())
      .then(({ photos }) => setPhotos(photos || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const refreshPhotos = async () => {
    const r = await fetch('/api/costumes');
    const d = await r.json();
    setPhotos(d.photos || []);
  };

  const onPick = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('guest_code', session.code);
      formData.append('guest_name', session.name);

      const res = await fetch('/api/costumes/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Upload failed. Please try again.');
      } else {
        await refreshPhotos();
      }
    } catch {
      setError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const deletePhoto = async (photoId: string) => {
    setDeletingId(photoId);
    try {
      const res = await fetch('/api/costumes', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: photoId, guest_code: session.code }),
      });
      if (res.ok) {
        await refreshPhotos();
      }
    } catch {
    } finally {
      setDeletingId(null);
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
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.gif,.webp,.heic,.heif,image/*"
            onChange={onPick}
            style={{ display: 'none' }}
            disabled={uploading}
          />
        </label>
        <div style={{ fontSize: 12, color: C.mint, marginTop: 8 }}>
          Birds, gods, or cowboys — show the group your costumes.
        </div>
        <div style={{ fontSize: 11, color: 'rgba(255,248,231,0.4)', marginTop: 4 }}>
          Supported: JPG, PNG, GIF, WebP, HEIC
        </div>
        {error && (
          <div
            style={{
              fontSize: 13,
              color: C.coral,
              marginTop: 10,
              background: 'rgba(255,100,80,0.1)',
              borderRadius: 8,
              padding: '8px 14px',
            }}
          >
            {error}
          </div>
        )}
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
                position: 'relative',
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
              {p.guest_code === session.code && (
                <button
                  onClick={() => deletePhoto(p.id)}
                  disabled={deletingId === p.id}
                  style={{
                    position: 'absolute',
                    top: 6,
                    right: 6,
                    background: 'rgba(0,0,0,0.6)',
                    color: C.cream,
                    border: 'none',
                    borderRadius: 6,
                    fontSize: 11,
                    padding: '3px 7px',
                    cursor: deletingId === p.id ? 'not-allowed' : 'pointer',
                    fontFamily: FONT,
                  }}
                >
                  {deletingId === p.id ? '…' : '✕'}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
