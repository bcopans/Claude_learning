'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import ProtectedLayout, { SessionWithRsvp } from '@/components/ProtectedLayout';
import { C, OFFERINGS, CALF_REACTIONS } from '@/lib/constants';

export default function ShrinePage() {
  return (
    <ProtectedLayout>
      {(session) => <ShrineContent session={session} />}
    </ProtectedLayout>
  );
}

const FONT = "'Space Grotesk', system-ui, sans-serif";

interface Offering {
  id: string;
  guest_name: string;
  offering_type: string;
  x_position: number;
  y_position: number;
  rotation: number;
  scale: number;
}

function ShrineContent({ session }: { session: SessionWithRsvp }) {
  const [offerings, setOfferings] = useState<Offering[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [reaction, setReaction] = useState<string | null>(null);
  const [legend, setLegend] = useState(false);
  const [muted, setMuted] = useState(false);
  const [loading, setLoading] = useState(true);
  const reactionTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const legendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    window.scrollTo(0, 0);
    fetchOfferings();
  }, []);

  const fetchOfferings = async () => {
    try {
      const res = await fetch('/api/offerings');
      const data = await res.json();
      setOfferings(data.offerings || []);
      setTotalCount(data.total || 0);
      // Build counts from loaded offerings
      const c: Record<string, number> = {};
      (data.offerings || []).forEach((o: Offering) => {
        c[o.offering_type] = (c[o.offering_type] || 0) + 1;
      });
      setCounts(c);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const playSound = useCallback(
    (crowdCheer = false) => {
      if (muted) return;
      const files = crowdCheer
        ? ['/sfx/crowd-cheer.wav']
        : ['/sfx/yass.wav', '/sfx/tongue-pop.wav', '/sfx/gay-gasp.wav', '/sfx/airhorn.wav', '/sfx/sparkle.wav'];
      const file = files[Math.floor(Math.random() * files.length)];
      try {
        const audio = new Audio(file);
        audio.play().catch(() => {});
      } catch {}
    },
    [muted]
  );

  const drop = async (type: string) => {
    const newTotal = totalCount + 1;
    const idx = offerings.length;
    const slot = idx % 6;
    const x = 28 + slot * 9 + (Math.random() * 4 - 2);
    const tier = Math.floor(idx / 6);
    const y = 68 + Math.random() * 6 + tier * 7;
    const rotation = -7 + Math.random() * 14;
    const scale = 0.82 + Math.random() * 0.16;

    const optimisticOffering: Offering = {
      id: `opt-${Date.now()}`,
      guest_name: session.name,
      offering_type: type,
      x_position: x,
      y_position: y,
      rotation,
      scale,
    };

    setOfferings((p) => [...p, optimisticOffering]);
    setTotalCount(newTotal);
    setCounts((p) => ({ ...p, [type]: (p[type] || 0) + 1 }));

    const reactionText = CALF_REACTIONS[Math.floor(Math.random() * CALF_REACTIONS.length)];
    setReaction(reactionText);
    if (reactionTimer.current) clearTimeout(reactionTimer.current);
    reactionTimer.current = setTimeout(() => setReaction(null), 2600);

    const isLegend = newTotal % 40 === 0;
    if (isLegend) {
      setLegend(true);
      if (legendTimer.current) clearTimeout(legendTimer.current);
      legendTimer.current = setTimeout(() => setLegend(false), 3500);
      playSound(true);
    } else {
      playSound(false);
    }

    try {
      await fetch('/api/offerings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guest_code: session.code,
          guest_name: session.name,
          offering_type: type,
          x_position: x,
          y_position: y,
          rotation,
          scale,
        }),
      });
    } catch {}
  };

  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  const topLabel = top ? OFFERINGS.find((o) => o.id === top[0])?.label : '—';
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  const maxRendered = isMobile ? 80 : 200;

  return (
    <div style={{ background: C.green, minHeight: 'calc(100vh - 49px)', padding: '40px 20px 60px' }}>
      <div style={{ maxWidth: 760, margin: '0 auto' }}>
        {/* Header */}
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
            Leave a tribute
          </div>
          <h1
            style={{
              fontFamily: "'Archivo Black', sans-serif",
              fontSize: 'clamp(26px,5vw,38px)',
              lineHeight: 1,
              textTransform: 'uppercase',
              color: C.cream,
              margin: '0 0 12px',
            }}
          >
            The Shrine
          </h1>
          <p style={{ fontSize: 15, color: C.mint, maxWidth: 420, margin: '0 auto', lineHeight: 1.6 }}>
            Lay an offering at the altar of the Golden Calf. He sees all. He judges gently.
          </p>
        </div>

        {/* Stats */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3,1fr)',
            gap: 10,
            marginBottom: 18,
          }}
        >
          {[
            ['Offerings', totalCount],
            ['Most loved', topLabel || '—'],
            ['Legend in', `${40 - (totalCount % 40 || 40)}`],
          ].map(([l, v], i) => (
            <div
              key={i}
              style={{
                background: 'rgba(255,248,231,0.07)',
                borderRadius: 12,
                padding: '12px 10px',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontFamily: "'Archivo Black', sans-serif",
                  fontSize: 18,
                  color: C.mango,
                }}
              >
                {v}
              </div>
              <div style={{ fontSize: 11, color: C.mint, marginTop: 2 }}>{l}</div>
            </div>
          ))}
        </div>

        {/* Sound toggle */}
        <div style={{ textAlign: 'right', marginBottom: 10 }}>
          <button
            onClick={() => setMuted((m) => !m)}
            style={{
              background: 'none',
              border: '0.5px solid rgba(255,248,231,0.3)',
              borderRadius: 6,
              color: C.mint,
              fontSize: 12,
              cursor: 'pointer',
              padding: '4px 10px',
              fontFamily: FONT,
            }}
          >
            {muted ? '🔇 Muted' : '🔊 Sound on'}
          </button>
        </div>

        {/* Calf */}
        <div style={{ position: 'relative', textAlign: 'center', marginBottom: 8 }}>
          {legend && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                zIndex: 25,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                pointerEvents: 'none',
              }}
            >
              <div
                style={{
                  fontFamily: "'Archivo Black', sans-serif",
                  fontSize: 38,
                  color: C.mango,
                  textShadow: `0 0 24px ${C.coral}, 0 0 8px #000`,
                  textAlign: 'center',
                  animation: 'legendPulse 0.5s ease infinite',
                }}
              >
                FORTY!
                <br />
                FORTY!
                <br />
                FORTY!
              </div>
            </div>
          )}
          <div
            style={{
              display: 'inline-block',
              position: 'relative',
              filter: `drop-shadow(0 0 ${legend ? '60px' : '40px'} rgba(255,182,39,${legend ? '0.7' : '0.45'}))`,
              transition: 'filter 0.5s',
            }}
          >
            <img
              src="/golden-calf.png"
              alt="The Golden Calf"
              style={{ width: 'min(320px,76%)', display: 'block', margin: '0 auto' }}
            />
            {reaction && (
              <div
                style={{
                  position: 'absolute',
                  top: 6,
                  right: -4,
                  zIndex: 12,
                  background: C.cream,
                  color: C.greenDeep,
                  padding: '8px 14px',
                  borderRadius: 16,
                  fontSize: 13,
                  fontWeight: 700,
                  maxWidth: 190,
                  fontFamily: FONT,
                  boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
                  animation: 'popIn 0.25s ease',
                }}
              >
                {reaction}
              </div>
            )}
          </div>
        </div>

        {/* Altar */}
        <div
          style={{
            textAlign: 'center',
            fontSize: 11,
            fontWeight: 700,
            color: C.mango,
            textTransform: 'uppercase',
            letterSpacing: '0.12em',
            marginBottom: 6,
          }}
        >
          Lay your tribute at the altar
        </div>
        <div style={{ position: 'relative', marginBottom: 18 }}>
          <img
            src="/altar.png"
            alt="The Altar of the Golden Calf"
            style={{ width: '100%', display: 'block' }}
          />
          <div
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              bottom: 0,
              top: 0,
              zIndex: 2,
              pointerEvents: 'none',
            }}
          >
            {offerings.slice(-maxRendered).map((o) => (
              <img
                key={o.id}
                src={`/offerings/${o.offering_type}.png`}
                alt=""
                title={`${OFFERINGS.find((x) => x.id === o.offering_type)?.label} — from ${o.guest_name}`}
                style={{
                  position: 'absolute',
                  left: `${o.x_position}%`,
                  bottom: `${o.y_position}%`,
                  width: '8%',
                  minWidth: 28,
                  maxWidth: 44,
                  transform: `translateX(-50%) rotate(${o.rotation}deg) scale(${o.scale})`,
                  transformOrigin: 'bottom center',
                  animation: o.id.startsWith('opt-') ? 'dropIn 0.45s cubic-bezier(.2,1.3,.4,1)' : undefined,
                  filter: 'drop-shadow(0 3px 4px rgba(0,0,0,0.45))',
                }}
              />
            ))}
          </div>
        </div>

        {/* Tray */}
        <div style={{ fontSize: 13, color: C.mint, textAlign: 'center', marginBottom: 12 }}>
          Tap an offering — credited to <strong style={{ color: C.cream }}>{session.name}</strong>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(96px,1fr))', gap: 10 }}>
          {OFFERINGS.map((o) => (
            <button
              key={o.id}
              onClick={() => drop(o.id)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(255,248,231,0.08)',
                border: '0.5px solid rgba(255,248,231,0.22)',
                borderRadius: 16,
                padding: '16px 8px',
                cursor: 'pointer',
                fontFamily: FONT,
                transition: 'transform 0.1s, background 0.15s',
              }}
              onMouseDown={(e) => ((e.currentTarget as HTMLElement).style.transform = 'scale(0.93)')}
              onMouseUp={(e) => ((e.currentTarget as HTMLElement).style.transform = 'scale(1)')}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.transform = 'scale(1)')}
            >
              <img
                src={`/offerings/${o.id}.png`}
                alt={o.label}
                style={{ width: 60, height: 60, objectFit: 'contain' }}
              />
              <div
                style={{ fontSize: 11, color: C.cream, marginTop: 8, lineHeight: 1.2, textAlign: 'center' }}
              >
                {o.label}
              </div>
              {counts[o.id] ? (
                <div style={{ fontSize: 11, color: C.mango, fontWeight: 700, marginTop: 2 }}>
                  ×{counts[o.id]}
                </div>
              ) : null}
            </button>
          ))}
        </div>

        {/* Feed */}
        {offerings.length > 0 && (
          <div style={{ marginTop: 18 }}>
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
              Latest tributes
            </div>
            {offerings
              .slice(-4)
              .reverse()
              .map((o) => (
                <div
                  key={o.id}
                  style={{
                    fontSize: 13,
                    color: C.mint,
                    padding: '4px 0',
                    borderBottom: '0.5px solid rgba(255,248,231,0.1)',
                  }}
                >
                  <strong style={{ color: C.cream }}>{o.guest_name}</strong> offered a{' '}
                  {OFFERINGS.find((x) => x.id === o.offering_type)?.label}{' '}
                  {OFFERINGS.find((x) => x.id === o.offering_type)?.emoji}
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
