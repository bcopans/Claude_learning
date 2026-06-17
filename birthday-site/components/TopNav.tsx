'use client';

import { usePathname, useRouter } from 'next/navigation';
import { clearSession } from '@/lib/auth';
import { C } from '@/lib/constants';
import { useEffect, useState } from 'react';

interface Props {
  rsvped: boolean;
  isAdmin?: boolean;
}

export default function TopNav({ rsvped, isAdmin }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const [showRsvpPing, setShowRsvpPing] = useState(false);

  useEffect(() => {
    // Show a subtle indicator on the RSVP button if not yet RSVPd
    setShowRsvpPing(!rsvped);
  }, [rsvped]);

  const goRsvp = () => {
    if (pathname === '/explore') {
      document.getElementById('rsvp')?.scrollIntoView({ behavior: 'smooth' });
    } else {
      router.push('/explore?section=rsvp');
    }
  };

  const signOut = () => {
    clearSession();
    router.push('/');
  };

  const navItem = (href: string, label: string, locked = false) => {
    const active = pathname === href;
    return (
      <button
        key={href}
        onClick={() => !locked && router.push(href)}
        style={{
          background: 'none',
          border: 'none',
          cursor: locked ? 'default' : 'pointer',
          fontFamily: "'Space Grotesk', system-ui, sans-serif",
          fontSize: 13,
          fontWeight: active ? 700 : 500,
          color: active ? C.mango : C.cream,
          padding: '4px 2px',
          opacity: locked ? 0.55 : 1,
        }}
      >
        {label}
        {locked ? ' 🔒' : ''}
      </button>
    );
  };

  return (
    <nav
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        background: C.green,
        padding: '12px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 8,
      }}
    >
      <button
        onClick={() => router.push('/home')}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: "'Archivo Black', sans-serif",
          fontSize: 15,
          color: C.cream,
          textTransform: 'uppercase',
        }}
      >
        Rio '27
      </button>
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        {navItem('/home', 'Ben')}
        {navItem('/explore', 'Explore')}
        {navItem('/shrine', 'Shrine')}
        {navItem('/members', 'Members', !rsvped)}
        {isAdmin && navItem('/admin', 'Admin')}
        {!rsvped && (
          <button
            onClick={goRsvp}
            style={{
              background: C.coral,
              border: 'none',
              borderRadius: 99,
              cursor: 'pointer',
              fontFamily: "'Space Grotesk', system-ui, sans-serif",
              fontSize: 12,
              fontWeight: 700,
              color: C.greenDeep,
              padding: '4px 12px',
            }}
          >
            RSVP →
          </button>
        )}
        <button
          onClick={signOut}
          style={{
            background: 'none',
            border: `1px solid rgba(255,248,231,0.3)`,
            cursor: 'pointer',
            fontFamily: "'Space Grotesk', system-ui, sans-serif",
            fontSize: 11,
            color: 'rgba(255,248,231,0.6)',
            padding: '3px 8px',
            borderRadius: 6,
          }}
        >
          sign out
        </button>
      </div>
    </nav>
  );
}
