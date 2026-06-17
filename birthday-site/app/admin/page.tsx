'use client';

import { useEffect, useState } from 'react';
import ProtectedLayout, { SessionWithRsvp } from '@/components/ProtectedLayout';
import { C, OFFERINGS } from '@/lib/constants';

export default function AdminPage() {
  return (
    <ProtectedLayout>
      {(session) => <AdminContent session={session} />}
    </ProtectedLayout>
  );
}

const FONT = "'Space Grotesk', system-ui, sans-serif";

interface Guest {
  code: string;
  name: string;
  active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface Rsvp {
  guest_code: string;
  name: string;
  attending: string;
  hotel: string;
  dietary: string;
  notes: string;
  created_at: string;
}

interface Stay {
  guest_code: string;
  name: string;
  hotel: string;
  arrive: string | null;
  depart: string | null;
}

interface Photo {
  name: string;
  image_url: string;
  created_at: string;
}

interface OfferingRow {
  guest_name: string;
  offering_type: string;
}

function AdminContent({ session }: { session: SessionWithRsvp }) {
  const [tab, setTab] = useState<'guests' | 'rsvps' | 'stays' | 'shrine'>('guests');

  const [guests, setGuests] = useState<Guest[]>([]);
  const [rsvps, setRsvps] = useState<Rsvp[]>([]);
  const [stays, setStays] = useState<Stay[]>([]);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [offerings, setOfferings] = useState<OfferingRow[]>([]);

  const [newName, setNewName] = useState('');
  const [newCode, setNewCode] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const authHeader = { 'x-guest-code': session.code };
  const jsonHeaders = { 'Content-Type': 'application/json', ...authHeader };

  const fetchGuests = async () => {
    const res = await fetch('/api/admin/guests', { headers: authHeader });
    const d = await res.json();
    setGuests(d.guests || []);
  };

  const fetchData = async () => {
    const res = await fetch('/api/admin/data', { headers: authHeader });
    if (!res.ok) return;
    const d = await res.json();
    setRsvps(d.rsvps || []);
    setStays(d.stays || []);
    setPhotos(d.costumes || []);
    setOfferings(d.offerings || []);
  };

  useEffect(() => {
    if (session.isAdmin) {
      fetchGuests();
      fetchData();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session.isAdmin]);

  if (!session.isAdmin) {
    return (
      <div
        style={{
          background: C.green,
          minHeight: 'calc(100vh - 49px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
          fontFamily: FONT,
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🔒</div>
          <div
            style={{
              fontFamily: "'Archivo Black', sans-serif",
              fontSize: 22,
              color: C.cream,
              textTransform: 'uppercase',
            }}
          >
            Admin only
          </div>
          <p style={{ color: C.mint, fontSize: 14, marginTop: 8 }}>
            You don't have admin access. Ask Ben.
          </p>
        </div>
      </div>
    );
  }

  const createGuest = async () => {
    setCreateError('');
    if (!newName.trim()) { setCreateError('Name required.'); return; }
    setCreating(true);
    const res = await fetch('/api/admin/guests', {
      method: 'POST',
      headers: jsonHeaders,
      body: JSON.stringify({ name: newName.trim(), code: newCode.trim() || undefined }),
    });
    const d = await res.json();
    if (!res.ok) {
      setCreateError(d.error || 'Error creating guest.');
    } else {
      setNewName('');
      setNewCode('');
      await fetchGuests();
    }
    setCreating(false);
  };

  const toggleActive = async (code: string, active: boolean) => {
    await fetch('/api/admin/guests', {
      method: 'PATCH',
      headers: jsonHeaders,
      body: JSON.stringify({ code, active }),
    });
    await fetchGuests();
  };

  const toggleAdmin = async (code: string, is_admin: boolean) => {
    await fetch('/api/admin/guests', {
      method: 'PATCH',
      headers: jsonHeaders,
      body: JSON.stringify({ code, is_admin }),
    });
    await fetchGuests();
  };

  const saveName = async (code: string) => {
    if (!editingName.trim()) return;
    setSavingEdit(true);
    await fetch('/api/admin/guests', {
      method: 'PATCH',
      headers: jsonHeaders,
      body: JSON.stringify({ code, name: editingName.trim() }),
    });
    setSavingEdit(false);
    setEditingCode(null);
    await fetchGuests();
  };

  const deleteGuest = async (code: string, name: string) => {
    if (!confirm(`Delete ${name} (${code})? This cannot be undone.`)) return;
    await fetch('/api/admin/guests', {
      method: 'DELETE',
      headers: jsonHeaders,
      body: JSON.stringify({ code }),
    });
    await fetchGuests();
  };

  const attending = rsvps.filter((r) => r.attending === 'yes');
  const notAttending = rsvps.filter((r) => r.attending === 'no');
  const hotelCounts: Record<string, number> = {};
  attending.forEach((r) => {
    if (r.hotel) hotelCounts[r.hotel] = (hotelCounts[r.hotel] || 0) + 1;
  });

  const offeringCounts: Record<string, number> = {};
  offerings.forEach((o) => {
    offeringCounts[o.offering_type] = (offeringCounts[o.offering_type] || 0) + 1;
  });

  const tabs: [string, string][] = [
    ['guests', '👥 Guests & Codes'],
    ['rsvps', '🎉 RSVPs'],
    ['stays', '🏨 Stays & Costumes'],
    ['shrine', '🐂 Shrine Activity'],
  ];

  const btn: React.CSSProperties = {
    padding: '4px 10px',
    borderRadius: 6,
    border: '1px solid #ccc',
    background: '#fff',
    fontSize: 12,
    cursor: 'pointer',
    fontFamily: FONT,
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 49px)', background: C.cream, fontFamily: FONT }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '24px 20px' }}>
        <div
          style={{
            fontFamily: "'Archivo Black', sans-serif",
            fontSize: 20,
            color: C.green,
            textTransform: 'uppercase',
            marginBottom: 20,
          }}
        >
          Rio '27 Admin
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 28 }}>
          {tabs.map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id as typeof tab)}
              style={{
                padding: '8px 14px',
                borderRadius: 99,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 700,
                fontFamily: FONT,
                border: tab === id ? `2px solid ${C.green}` : '1px solid #ccc',
                background: tab === id ? C.green : '#fff',
                color: tab === id ? C.cream : C.green,
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* GUESTS TAB */}
        {tab === 'guests' && (
          <div>
            <h2 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 22, color: C.green, marginBottom: 20, textTransform: 'uppercase' }}>
              Guest Codes
            </h2>

            <div
              style={{
                background: '#fff',
                border: '1px solid #ddd',
                borderRadius: 12,
                padding: 20,
                marginBottom: 24,
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 14, color: C.green }}>
                Add a friend
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 10, alignItems: 'end' }}>
                <div>
                  <label style={{ fontSize: 12, color: '#666', display: 'block', marginBottom: 4 }}>Name *</label>
                  <input
                    value={newName}
                    onChange={(e) => { setNewName(e.target.value); setCreateError(''); }}
                    onKeyDown={(e) => e.key === 'Enter' && createGuest()}
                    placeholder="Dalton"
                    style={{ width: '100%', padding: '10px 12px', border: '1px solid #ccc', borderRadius: 8, fontSize: 16, fontFamily: FONT, boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: '#666', display: 'block', marginBottom: 4 }}>Code (auto-gen if blank)</label>
                  <input
                    value={newCode}
                    onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                    placeholder="BEN-DALTON"
                    style={{ width: '100%', padding: '10px 12px', border: '1px solid #ccc', borderRadius: 8, fontSize: 16, fontFamily: FONT, boxSizing: 'border-box', textTransform: 'uppercase' }}
                  />
                </div>
                <button
                  onClick={createGuest}
                  disabled={creating}
                  style={{ padding: '10px 18px', background: C.green, color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 14, cursor: creating ? 'not-allowed' : 'pointer', fontFamily: FONT, whiteSpace: 'nowrap' }}
                >
                  {creating ? '…' : 'Add →'}
                </button>
              </div>
              {createError && <div style={{ color: C.coral, fontSize: 13, marginTop: 8 }}>{createError}</div>}
              <p style={{ fontSize: 12, color: '#888', margin: '10px 0 0' }}>
                The code is what your friend enters at the gate. It's tied to their name.
              </p>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                <thead>
                  <tr style={{ background: C.green, color: C.cream }}>
                    {['Name', 'Code', 'Status', 'Admin', 'Added', 'Actions'].map((h) => (
                      <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontFamily: "'Archivo Black', sans-serif", fontSize: 12, letterSpacing: '0.05em' }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {guests.map((g, i) => (
                    <tr key={g.code} style={{ background: i % 2 === 0 ? '#fff' : '#f8f5ee', borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '10px 14px', fontWeight: 700 }}>
                        {editingCode === g.code ? (
                          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                            <input
                              value={editingName}
                              onChange={(e) => setEditingName(e.target.value)}
                              onKeyDown={(e) => e.key === 'Enter' && saveName(g.code)}
                              autoFocus
                              style={{ padding: '4px 8px', border: '1px solid #aaa', borderRadius: 6, fontSize: 14, fontFamily: FONT, width: 120 }}
                            />
                            <button onClick={() => saveName(g.code)} disabled={savingEdit} style={{ ...btn, background: C.green, color: '#fff', border: 'none' }}>
                              {savingEdit ? '…' : 'Save'}
                            </button>
                            <button onClick={() => setEditingCode(null)} style={btn}>✕</button>
                          </div>
                        ) : (
                          <span>{g.name}</span>
                        )}
                      </td>
                      <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontSize: 13, background: '#f0f0f0', userSelect: 'all' }}>
                        {g.code}
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 99, background: g.active ? '#dcf5e9' : '#fee', color: g.active ? '#0a5c35' : '#c00' }}>
                          {g.active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        {g.is_admin && (
                          <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 99, background: '#e8f0fe', color: '#1a56db' }}>
                            Admin
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '10px 14px', fontSize: 12, color: '#888' }}>
                        {new Date(g.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          <button
                            onClick={() => { setEditingCode(g.code); setEditingName(g.name); }}
                            style={btn}
                          >
                            Edit name
                          </button>
                          <button onClick={() => toggleActive(g.code, !g.active)} style={btn}>
                            {g.active ? 'Deactivate' : 'Reactivate'}
                          </button>
                          <button
                            onClick={() => toggleAdmin(g.code, !g.is_admin)}
                            style={{ ...btn, color: g.is_admin ? '#c00' : '#1a56db', borderColor: g.is_admin ? '#fcc' : '#b3c6f7' }}
                          >
                            {g.is_admin ? 'Remove admin' : 'Make admin'}
                          </button>
                          {g.code !== session.code && (
                            <button
                              onClick={() => deleteGuest(g.code, g.name)}
                              style={{ ...btn, border: '1px solid #fcc', background: '#fff8f8', color: '#c00' }}
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {guests.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ padding: 20, textAlign: 'center', color: '#888' }}>
                        No guests yet. Add one above.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* RSVPS TAB */}
        {tab === 'rsvps' && (
          <div>
            <h2 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 22, color: C.green, marginBottom: 8, textTransform: 'uppercase' }}>
              RSVPs
            </h2>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
              {[
                ['Coming', attending.length, C.green],
                ['Not coming', notAttending.length, C.coral],
                ['Fasano', hotelCounts['fasano'] || 0, C.mango],
                ['Arpoador', hotelCounts['arpoador'] || 0, C.mango],
              ].map(([l, v, col]) => (
                <div key={String(l)} style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 10, padding: '12px 18px', textAlign: 'center', minWidth: 90 }}>
                  <div style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 24, color: String(col) }}>{String(v)}</div>
                  <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{String(l)}</div>
                </div>
              ))}
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: C.green, color: C.cream }}>
                    {['Name', 'Attending', 'Hotel', 'Dietary', 'Notes', 'Date'].map((h) => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontFamily: "'Archivo Black', sans-serif", fontSize: 11 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rsvps.map((r, i) => (
                    <tr key={r.guest_code} style={{ background: i % 2 === 0 ? '#fff' : '#f8f5ee', borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 700 }}>{r.name}</td>
                      <td style={{ padding: '9px 12px' }}>
                        <span style={{ fontWeight: 700, color: r.attending === 'yes' ? '#0a5c35' : C.coral }}>
                          {r.attending === 'yes' ? '✓ Yes' : '✗ No'}
                        </span>
                      </td>
                      <td style={{ padding: '9px 12px' }}>{r.hotel || '—'}</td>
                      <td style={{ padding: '9px 12px' }}>{r.dietary || '—'}</td>
                      <td style={{ padding: '9px 12px', maxWidth: 200, fontSize: 12, color: '#555' }}>{r.notes || '—'}</td>
                      <td style={{ padding: '9px 12px', fontSize: 11, color: '#888' }}>{new Date(r.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                  {rsvps.length === 0 && (
                    <tr><td colSpan={6} style={{ padding: 20, textAlign: 'center', color: '#888' }}>No RSVPs yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* STAYS & COSTUMES TAB */}
        {tab === 'stays' && (
          <div>
            <h2 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 22, color: C.green, marginBottom: 20, textTransform: 'uppercase' }}>
              Stays
            </h2>
            {stays.length === 0 ? (
              <p style={{ color: '#888' }}>No stays posted yet.</p>
            ) : (
              <div style={{ display: 'grid', gap: 10, marginBottom: 32 }}>
                {stays.map((s, i) => (
                  <div key={i} style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 10, padding: '12px 16px', display: 'flex', gap: 12, alignItems: 'center' }}>
                    <div style={{ fontWeight: 700, flex: 1 }}>{s.name}</div>
                    <div style={{ color: C.green, fontWeight: 700 }}>{s.hotel}</div>
                    <div style={{ fontSize: 13, color: '#888' }}>{s.arrive || '?'} → {s.depart || '?'}</div>
                  </div>
                ))}
              </div>
            )}

            <h2 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 22, color: C.green, marginBottom: 16, textTransform: 'uppercase' }}>
              Costume Wall
            </h2>
            {photos.length === 0 ? (
              <p style={{ color: '#888' }}>No costume photos yet.</p>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px,1fr))', gap: 10 }}>
                {photos.map((p, i) => (
                  <div key={i} style={{ borderRadius: 10, overflow: 'hidden', border: '1px solid #ddd' }}>
                    <img src={p.image_url} alt="costume" style={{ width: '100%', height: 160, objectFit: 'cover', display: 'block' }} />
                    <div style={{ fontSize: 12, padding: '6px 8px', fontWeight: 700 }}>{p.name}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* SHRINE TAB */}
        {tab === 'shrine' && (
          <div>
            <h2 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 22, color: C.green, marginBottom: 8, textTransform: 'uppercase' }}>
              Shrine Activity
            </h2>
            <p style={{ color: '#666', marginBottom: 20 }}>Total offerings: <strong>{offerings.length}</strong></p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px,1fr))', gap: 10, marginBottom: 28 }}>
              {OFFERINGS.map((o) => (
                <div key={o.id} style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 10, padding: '12px 14px', textAlign: 'center' }}>
                  <img src={`/offerings/${o.id}.png`} alt={o.label} style={{ width: 48, height: 48, objectFit: 'contain', marginBottom: 6 }} />
                  <div style={{ fontSize: 13, fontWeight: 700, color: C.green }}>{o.label}</div>
                  <div style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 22, color: C.mango, marginTop: 4 }}>
                    {offeringCounts[o.id] || 0}
                  </div>
                </div>
              ))}
            </div>

            <h3 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 16, color: C.green, marginBottom: 12 }}>
              By guest
            </h3>
            <div style={{ overflowX: 'auto' }}>
              {(() => {
                const byGuest: Record<string, number> = {};
                offerings.forEach((o) => { byGuest[o.guest_name] = (byGuest[o.guest_name] || 0) + 1; });
                return (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ background: C.green, color: C.cream }}>
                        {['Guest', 'Offerings'].map((h) => (
                          <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontFamily: "'Archivo Black', sans-serif", fontSize: 11 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(byGuest).sort((a, b) => b[1] - a[1]).map(([name, count], i) => (
                        <tr key={name} style={{ background: i % 2 === 0 ? '#fff' : '#f8f5ee' }}>
                          <td style={{ padding: '8px 12px', fontWeight: 700 }}>{name}</td>
                          <td style={{ padding: '8px 12px' }}>{count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                );
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
