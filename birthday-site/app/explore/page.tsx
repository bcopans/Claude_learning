'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import ProtectedLayout, { SessionWithRsvp } from '@/components/ProtectedLayout';
import { C, FAQ, ITIN, SAFETY } from '@/lib/constants';

export default function ExplorePage() {
  return (
    <ProtectedLayout>
      {(session) => (
        <Suspense>
          <ExploreContent session={session} />
        </Suspense>
      )}
    </ProtectedLayout>
  );
}

const FONT = "'Space Grotesk', system-ui, sans-serif";

function Sec({
  id,
  bg,
  children,
}: {
  id?: string;
  bg: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} style={{ background: bg, padding: '56px 0' }}>
      <div style={{ maxWidth: 760, margin: '0 auto', padding: '0 20px' }}>{children}</div>
    </section>
  );
}

function Eyebrow({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <div
      style={{
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: '0.15em',
        textTransform: 'uppercase',
        color: color || C.coral,
        marginBottom: 14,
      }}
    >
      {children}
    </div>
  );
}

function H2({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <h2
      style={{
        fontFamily: "'Archivo Black', sans-serif",
        fontSize: 'clamp(26px,5vw,38px)',
        lineHeight: 1,
        textTransform: 'uppercase',
        color: color || C.green,
        margin: '0 0 20px',
      }}
    >
      {children}
    </h2>
  );
}

function ExploreContent({ session }: { session: SessionWithRsvp }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [rsvped, setRsvped] = useState(session.rsvped || false);
  const [rsvpForm, setRsvpForm] = useState({ attend: '', hotel: '', dietary: '', notes: '' });
  const [rsvpDone, setRsvpDone] = useState(false);
  const [rsvpErr, setRsvpErr] = useState('');
  const [rsvpLoading, setRsvpLoading] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
    // Check if we should scroll to RSVP section
    if (searchParams.get('section') === 'rsvp') {
      setTimeout(() => {
        document.getElementById('rsvp')?.scrollIntoView({ behavior: 'smooth' });
      }, 200);
    }
  }, [searchParams]);

  useEffect(() => {
    // Check existing RSVP
    fetch(`/api/rsvp?code=${session.code}`)
      .then((r) => r.json())
      .then(({ rsvp }) => {
        if (rsvp) {
          setRsvpForm({
            attend: rsvp.attending,
            hotel: rsvp.hotel || '',
            dietary: rsvp.dietary || '',
            notes: rsvp.notes || '',
          });
          if (rsvp.attending === 'yes') {
            setRsvped(true);
            setRsvpDone(true);
            localStorage.setItem(`rio27_rsvped_${session.code}`, 'yes');
          } else if (rsvp.attending === 'no') {
            setRsvpDone(true);
          }
        }
      })
      .catch(() => {});
  }, [session.code]);

  const submitRsvp = async () => {
    if (!rsvpForm.attend) {
      setRsvpErr('Let us know if you\'re coming!');
      return;
    }
    setRsvpLoading(true);
    setRsvpErr('');
    try {
      const res = await fetch('/api/rsvp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guest_code: session.code,
          name: session.name,
          attending: rsvpForm.attend,
          hotel: rsvpForm.hotel,
          dietary: rsvpForm.dietary,
          notes: rsvpForm.notes,
        }),
      });
      if (!res.ok) {
        const d = await res.json();
        setRsvpErr(d.error || 'Something went wrong.');
        return;
      }
      setRsvpDone(true);
      if (rsvpForm.attend === 'yes') {
        setRsvped(true);
        localStorage.setItem(`rio27_rsvped_${session.code}`, 'yes');
      }
    } catch {
      setRsvpErr('Network error. Try again.');
    } finally {
      setRsvpLoading(false);
    }
  };

  const il: React.CSSProperties = {
    width: '100%',
    padding: '11px 14px',
    border: `0.5px solid #1d6b54`,
    borderRadius: 8,
    fontSize: 16,
    fontFamily: FONT,
    color: C.cream,
    background: 'rgba(255,248,231,0.06)',
    outline: 'none',
    marginTop: 6,
    boxSizing: 'border-box',
  };

  return (
    <div>
      {/* FAQ */}
      <Sec id="intro" bg={C.cream}>
        <Eyebrow>First time at Carnival? Read this</Eyebrow>
        <H2>
          What you're
          <br />
          signing up for
        </H2>
        <p
          style={{ fontSize: 16, lineHeight: 1.7, color: '#4A3A28', maxWidth: 600, marginBottom: 20 }}
        >
          Rio Carnival is the biggest party on the planet — around two million people on the streets
          every day. Here's the lay of the land so nobody shows up confused.
        </p>
        {FAQ.map((f, i) => (
          <details key={i} style={{ borderBottom: '0.5px solid #E0D2B0', padding: '14px 0' }}>
            <summary
              style={{
                fontSize: 16,
                fontWeight: 700,
                color: C.green,
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              {f.q}
              <span style={{ color: C.coral, fontSize: 20 }}>+</span>
            </summary>
            <p style={{ fontSize: 15, lineHeight: 1.7, color: '#5A4A38', marginTop: 10 }}>{f.a}</p>
          </details>
        ))}
      </Sec>

      {/* Itinerary */}
      <Sec id="plan" bg={C.green}>
        <Eyebrow color={C.mango}>The plan</Eyebrow>
        <H2 color={C.cream}>Eight days in Rio</H2>
        {ITIN.map(([d, t], i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              gap: 16,
              padding: '13px 0',
              borderBottom: '0.5px solid rgba(255,248,231,0.15)',
            }}
          >
            <div style={{ minWidth: 90, fontSize: 13, fontWeight: 700, color: C.cream }}>{d}</div>
            <div style={{ fontSize: 15, color: C.mint }}>{t}</div>
          </div>
        ))}
      </Sec>

      {/* Hotels */}
      <Sec id="stay" bg={C.cream}>
        <Eyebrow>Where we're staying</Eyebrow>
        <H2>Home base: Ipanema</H2>
        <p
          style={{
            fontSize: 15,
            lineHeight: 1.7,
            color: '#4A3A28',
            maxWidth: 600,
            marginBottom: 20,
          }}
        >
          We're basing the group in Ipanema — steps from the gay beach, the Banda de Ipanema route,
          and the Farme de Amoedo bar strip. Two options, a five-minute walk apart.
        </p>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px,1fr))',
            gap: 14,
          }}
        >
          {[
            [
              'Hotel Fasano',
              'Luxury · ~$700+/nt',
              'Beachfront, rooftop infinity pool, birthday HQ. Book via Amex FHR for breakfast + $150 spa credit.',
            ],
            [
              'Hotel Arpoador',
              'Mid-luxury · ~$350–500/nt',
              'Rooftop pool rivaling Fasano at a friendlier price. 3 min walk away — great overflow.',
            ],
          ].map(([n, tier, d], i) => (
            <div
              key={i}
              style={{
                background: '#fff',
                border: '0.5px solid #E8D9B0',
                borderRadius: 14,
                padding: 18,
              }}
            >
              <div
                style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: 17, color: C.green }}
              >
                {n}
              </div>
              <div style={{ fontSize: 12, color: C.coral, fontWeight: 700, margin: '3px 0 10px' }}>
                {tier}
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.6, color: '#5A4A38' }}>{d}</div>
            </div>
          ))}
        </div>
      </Sec>

      {/* Costumes */}
      <Sec id="costumes" bg={C.green}>
        <Eyebrow color={C.mango}>Dress the part</Eyebrow>
        <H2 color={C.cream}>Three nights, three looks</H2>
        <p style={{ fontSize: 15, color: C.mint, lineHeight: 1.7, marginBottom: 20 }}>
          One group theme per big night. Do your own version — a different bird, a different god,
          your own cowboy. It's hot (95–100°F), so less fabric is genuinely better.
        </p>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))',
            gap: 12,
          }}
        >
          {[
            ['🤠', 'Sat Feb 6 · Circuit', 'Cowboys of Copacabana'],
            ['🪶', 'Sun Feb 7 · Banda', 'Tropical Birds of Paradise'],
            ['🏛️', 'Tue Feb 9 · Sambadrome', 'Greek Gods of Ipanema'],
          ].map(([e, night, name], i) => (
            <div
              key={i}
              style={{
                background: 'rgba(255,248,231,0.07)',
                border: '0.5px solid rgba(255,248,231,0.2)',
                borderRadius: 14,
                padding: 18,
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: 34, marginBottom: 8 }}>{e}</div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  color: C.mango,
                  marginBottom: 6,
                }}
              >
                {night}
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.cream }}>{name}</div>
            </div>
          ))}
        </div>
      </Sec>

      {/* Safety */}
      <Sec id="safety" bg={C.cream}>
        <Eyebrow>Good to know</Eyebrow>
        <H2>
          Stay safe,
          <br />
          have fun
        </H2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px,1fr))',
            gap: 14,
            marginTop: 6,
          }}
        >
          {SAFETY.map((s, i) => (
            <div
              key={i}
              style={{
                background: '#fff',
                border: '0.5px solid #E8D9B0',
                borderRadius: 14,
                padding: 18,
              }}
            >
              <div style={{ fontSize: 24, marginBottom: 8 }}>{s.icon}</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: C.green, marginBottom: 4 }}>
                {s.title}
              </div>
              <div style={{ fontSize: 13, lineHeight: 1.6, color: '#5A4A38' }}>{s.text}</div>
            </div>
          ))}
        </div>
      </Sec>

      {/* Budget */}
      <Sec id="budget" bg={C.mango}>
        <Eyebrow color={C.greenDeep}>The money talk</Eyebrow>
        <H2 color={C.greenDeep}>What to budget</H2>
        <p
          style={{
            fontSize: 17,
            lineHeight: 1.7,
            color: '#5F4A1A',
            fontWeight: 500,
            marginBottom: 18,
          }}
        >
          Plan for{' '}
          <strong style={{ color: C.greenDeep }}>$5,000–8,000 per person</strong>, depending on
          flight class and hotel, sharing a room.
        </p>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px,1fr))',
            gap: 10,
          }}
        >
          {[
            ['Flights (RT)', '$1,000–3,500'],
            ['Hotel (9 nts, shared)', '$1,800–3,600'],
            ['Camarote (Feb 9)', '$560–1,050'],
            ['2 circuit parties', '$160–300'],
            ['Food + Ubers', '$700–1,600'],
            ['Sights + costume', '$200–500'],
          ].map(([l, v], i) => (
            <div
              key={i}
              style={{ background: 'rgba(11,77,60,0.08)', borderRadius: 10, padding: '12px 14px' }}
            >
              <div style={{ fontSize: 12, color: '#5F4A1A', marginBottom: 3 }}>{l}</div>
              <div
                style={{
                  fontFamily: "'Archivo Black', sans-serif",
                  fontSize: 16,
                  color: C.greenDeep,
                }}
              >
                {v}
              </div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: '#5F4A1A', marginTop: 16 }}>
          Want your own room? Add the full hotel rate again. Book flights by{' '}
          <strong>early November 2026</strong> — February is peak season and fares spike from
          December.
        </p>
      </Sec>

      {/* RSVP */}
      <Sec id="rsvp" bg={C.greenDeep}>
        {rsvpDone ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: 48, marginBottom: 14 }}>🎉</div>
            <h2
              style={{
                fontFamily: "'Archivo Black', sans-serif",
                fontSize: 'clamp(26px,5vw,38px)',
                lineHeight: 1,
                textTransform: 'uppercase',
                color: C.cream,
                margin: '0 0 20px',
              }}
            >
              You're on the list!
            </h2>
            <p
              style={{
                fontSize: 16,
                color: C.mint,
                maxWidth: 380,
                margin: '0 auto 22px',
                lineHeight: 1.6,
              }}
            >
              {rsvpForm.attend === 'no'
                ? 'Noted with love. The Calf understands.'
                : 'The members area is now unlocked — who\'s staying where, and the costume wall.'}
            </p>
            {rsvpForm.attend !== 'no' && (
              <button
                onClick={() => router.push('/members')}
                style={{
                  background: C.mango,
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
                Enter Members Area →
              </button>
            )}
          </div>
        ) : (
          <>
            <div style={{ textAlign: 'center', marginBottom: 26 }}>
              <Eyebrow color={C.mango}>Are you in, {session.name}?</Eyebrow>
              <H2 color={C.cream}>RSVP</H2>
              <p
                style={{
                  fontSize: 15,
                  color: C.mint,
                  maxWidth: 420,
                  margin: '0 auto',
                  lineHeight: 1.6,
                }}
              >
                Reply by <strong style={{ color: C.coral }}>July 31, 2026</strong>. RSVPing yes
                unlocks the members area.
              </p>
            </div>
            <div style={{ maxWidth: 520, margin: '0 auto' }}>
              <div style={{ marginBottom: 18 }}>
                <label
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: C.cream,
                    display: 'block',
                  }}
                >
                  Are you coming?
                </label>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 8,
                    marginTop: 6,
                  }}
                >
                  {[
                    ['yes', "🎉 I'm coming!"],
                    ['no', "😢 Can't make it"],
                  ].map(([v, l]) => (
                    <button
                      key={v}
                      onClick={() => setRsvpForm({ ...rsvpForm, attend: v })}
                      style={{
                        padding: 12,
                        borderRadius: 8,
                        cursor: 'pointer',
                        fontSize: 14,
                        fontWeight: 700,
                        fontFamily: FONT,
                        border:
                          rsvpForm.attend === v
                            ? `1.5px solid ${C.mango}`
                            : '0.5px solid #1d6b54',
                        background:
                          rsvpForm.attend === v ? 'rgba(255,182,39,0.15)' : 'rgba(255,248,231,0.06)',
                        color: rsvpForm.attend === v ? C.mango : C.mint,
                      }}
                    >
                      {l}
                    </button>
                  ))}
                </div>
              </div>

              {rsvpForm.attend === 'yes' && (
                <>
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ fontSize: 13, fontWeight: 700, color: C.cream, display: 'block' }}>
                      Hotel preference
                    </label>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr 1fr',
                        gap: 8,
                        marginTop: 6,
                      }}
                    >
                      {[
                        ['fasano', 'Fasano'],
                        ['arpoador', 'Arpoador'],
                        ['tbd', 'Not sure'],
                      ].map(([v, l]) => (
                        <button
                          key={v}
                          onClick={() => setRsvpForm({ ...rsvpForm, hotel: v })}
                          style={{
                            padding: '10px 8px',
                            borderRadius: 8,
                            cursor: 'pointer',
                            fontSize: 13,
                            fontWeight: 500,
                            fontFamily: FONT,
                            border:
                              rsvpForm.hotel === v
                                ? `1.5px solid ${C.mango}`
                                : '0.5px solid #1d6b54',
                            background:
                              rsvpForm.hotel === v
                                ? 'rgba(255,182,39,0.15)'
                                : 'rgba(255,248,231,0.06)',
                            color: rsvpForm.hotel === v ? C.mango : C.mint,
                          }}
                        >
                          {l}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ fontSize: 13, fontWeight: 700, color: C.cream, display: 'block' }}>
                      Dietary restrictions
                    </label>
                    <input
                      style={il}
                      value={rsvpForm.dietary}
                      onChange={(e) => setRsvpForm({ ...rsvpForm, dietary: e.target.value })}
                      placeholder="Vegetarian, allergies, none…"
                    />
                  </div>
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ fontSize: 13, fontWeight: 700, color: C.cream, display: 'block' }}>
                      Notes for Ben (optional)
                    </label>
                    <textarea
                      style={{ ...il, minHeight: 80, resize: 'vertical' }}
                      value={rsvpForm.notes}
                      onChange={(e) => setRsvpForm({ ...rsvpForm, notes: e.target.value })}
                      placeholder="Anything else Ben should know…"
                    />
                  </div>
                </>
              )}

              {rsvpErr && (
                <div
                  style={{ color: C.coral, fontSize: 13, textAlign: 'center', marginBottom: 10 }}
                >
                  {rsvpErr}
                </div>
              )}
              <button
                onClick={submitRsvp}
                disabled={rsvpLoading}
                style={{
                  width: '100%',
                  padding: 15,
                  background: rsvpLoading ? '#a04040' : C.coral,
                  color: C.greenDeep,
                  border: 'none',
                  borderRadius: 8,
                  fontFamily: FONT,
                  fontSize: 15,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  cursor: rsvpLoading ? 'not-allowed' : 'pointer',
                }}
              >
                {rsvpLoading ? 'Saving…' : 'Count me in →'}
              </button>
            </div>
          </>
        )}
      </Sec>
    </div>
  );
}
