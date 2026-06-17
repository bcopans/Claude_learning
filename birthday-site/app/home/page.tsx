'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedLayout from '@/components/ProtectedLayout';
import { C, GOSPEL } from '@/lib/constants';

export default function HomePage() {
  return (
    <ProtectedLayout>
      {(_session) => <HomeContent />}
    </ProtectedLayout>
  );
}

function HomeContent() {
  const router = useRouter();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div style={{ background: C.greenDeep, minHeight: 'calc(100vh - 49px)' }}>
      <div
        style={{
          position: 'relative',
          overflow: 'hidden',
          padding: '48px 20px 30px',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: -40,
            right: -40,
            width: 180,
            height: 180,
            borderRadius: '50%',
            background: C.coral,
            opacity: 0.85,
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: -50,
            left: -40,
            width: 150,
            height: 150,
            borderRadius: '50%',
            background: C.mango,
            opacity: 0.8,
          }}
        />
        <div style={{ position: 'relative', zIndex: 2 }}>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              color: C.mango,
              marginBottom: 14,
            }}
          >
            You're invited · Rio · Feb 3–12, 2027
          </div>
          <h1
            style={{
              fontFamily: "'Archivo Black', sans-serif",
              fontSize: 'clamp(30px,7vw,52px)',
              lineHeight: 0.95,
              textTransform: 'uppercase',
              color: C.cream,
              margin: '0 0 12px',
            }}
          >
            The Gospel of
            <br />
            the Golden Calf
          </h1>
          <p
            style={{
              fontSize: 15,
              color: C.mint,
              maxWidth: 440,
              margin: '0 auto 20px',
              lineHeight: 1.6,
            }}
          >
            Ben turns 40, and you're invited to worship in Rio. First, a brief scripture. Then:
            explore the trip, or leave an offering.
          </p>
          <div
            style={{
              maxWidth: 440,
              margin: '0 auto',
              borderRadius: 16,
              overflow: 'hidden',
              border: `2px solid ${C.mango}`,
              boxShadow: '0 0 50px rgba(255,182,39,0.3)',
            }}
          >
            <img
              src="/golden-calf.png"
              alt="The Golden Calf"
              style={{ width: '100%', display: 'block' }}
            />
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 600, margin: '0 auto', padding: '10px 20px 40px' }}>
        {GOSPEL.map((line, i) => (
          <p
            key={i}
            style={{
              fontSize: i === 0 ? 20 : 16,
              lineHeight: 1.7,
              color: i === 0 ? C.mango : C.mint,
              fontStyle: i === 0 ? 'italic' : 'normal',
              fontWeight: i === 0 ? 700 : 400,
              marginBottom: 16,
              textAlign: i === 0 ? 'center' : 'left',
            }}
          >
            {line}
          </p>
        ))}

        <div style={{ textAlign: 'center', margin: '24px 0 32px' }}>
          <span
            style={{
              fontFamily: "'Archivo Black', sans-serif",
              fontSize: 13,
              letterSpacing: '0.1em',
              color: C.coral,
              textTransform: 'uppercase',
            }}
          >
            Charisma · Uniqueness · Nerve · Talent
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <button
            onClick={() => router.push('/explore')}
            style={{
              background: C.cream,
              color: C.greenDeep,
              border: 'none',
              borderRadius: 14,
              padding: '22px 16px',
              cursor: 'pointer',
              fontFamily: "'Space Grotesk', system-ui, sans-serif",
              textAlign: 'left',
            }}
          >
            <div style={{ fontSize: 26, marginBottom: 6 }}>🌴</div>
            <div
              style={{
                fontFamily: "'Archivo Black', sans-serif",
                fontSize: 16,
                textTransform: 'uppercase',
                marginBottom: 4,
              }}
            >
              Explore the trip
            </div>
            <div style={{ fontSize: 12, color: '#5A4A38', lineHeight: 1.5 }}>
              Itinerary, hotels, costumes, budget — and RSVP →
            </div>
          </button>
          <button
            onClick={() => router.push('/shrine')}
            style={{
              background: C.mango,
              color: C.greenDeep,
              border: 'none',
              borderRadius: 14,
              padding: '22px 16px',
              cursor: 'pointer',
              fontFamily: "'Space Grotesk', system-ui, sans-serif",
              textAlign: 'left',
            }}
          >
            <div style={{ fontSize: 26, marginBottom: 6 }}>🐂</div>
            <div
              style={{
                fontFamily: "'Archivo Black', sans-serif",
                fontSize: 16,
                textTransform: 'uppercase',
                marginBottom: 4,
              }}
            >
              Visit the Shrine
            </div>
            <div style={{ fontSize: 12, color: '#5F4A1A', lineHeight: 1.5 }}>
              Leave an offering at the altar of the Calf →
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
