'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getSession, setSession, clearSession } from '@/lib/auth';
import { C } from '@/lib/constants';

export default function GateClient() {
  const router = useRouter();
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const session = getSession();
    if (session) {
      router.replace('/home');
    } else {
      setChecking(false);
    }
  }, [router]);

  const submit = async () => {
    const trimmed = code.trim().toUpperCase();
    if (!trimmed) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/auth/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: trimmed }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Invalid code.');
        setLoading(false);
        return;
      }
      setSession({ code: data.code, name: data.name });
      router.push('/home');
    } catch {
      setError('Something went wrong. Try again.');
      setLoading(false);
    }
  };

  if (checking) return null;

  return (
    <div
      style={{
        fontFamily: "'Space Grotesk', system-ui, sans-serif",
        minHeight: '100vh',
        background: `radial-gradient(circle at 50% 30%, rgba(255,182,39,0.18), ${C.greenDeep})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <div style={{ maxWidth: 420, width: '100%', textAlign: 'center' }}>
        <img
          src="/golden-calf.png"
          alt="The Golden Calf"
          style={{
            width: 130,
            height: 130,
            objectFit: 'cover',
            borderRadius: '50%',
            border: `3px solid ${C.mango}`,
            marginBottom: 14,
          }}
        />
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: C.mango,
            marginBottom: 12,
          }}
        >
          You're invited · Ben's 40th
        </div>
        <h1
          style={{
            fontFamily: "'Archivo Black', sans-serif",
            fontSize: 30,
            lineHeight: 1,
            textTransform: 'uppercase',
            color: C.cream,
            margin: '0 0 10px',
          }}
        >
          You're invited to Rio
        </h1>
        <p style={{ fontSize: 14, color: C.mint, lineHeight: 1.6, margin: '0 0 22px' }}>
          Join Ben for his 40th at Carnival, Feb 3–12, 2027. Enter the personal code from your
          invite to come inside.
        </p>
        <input
          value={code}
          onChange={(e) => {
            setCode(e.target.value);
            setError('');
          }}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="YOUR-CODE"
          autoCapitalize="characters"
          style={{
            width: '100%',
            padding: '14px 16px',
            borderRadius: 10,
            textAlign: 'center',
            border: `1px solid ${error ? C.coral : '#1d6b54'}`,
            background: 'rgba(255,248,231,0.07)',
            color: C.cream,
            fontSize: 18,
            fontWeight: 700,
            letterSpacing: '0.08em',
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
            boxSizing: 'border-box',
            textTransform: 'uppercase',
            outline: 'none',
          }}
        />
        {error && (
          <div style={{ color: C.coral, fontSize: 13, marginTop: 10 }}>{error}</div>
        )}
        <button
          onClick={submit}
          disabled={loading}
          style={{
            marginTop: 16,
            width: '100%',
            padding: 14,
            background: loading ? '#a04040' : C.coral,
            color: C.greenDeep,
            border: 'none',
            borderRadius: 10,
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
            fontSize: 15,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Checking…' : 'Enter →'}
        </button>
      </div>
    </div>
  );
}
