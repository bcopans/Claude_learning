'use client';

import { usePathname, useRouter } from 'next/navigation';
import { clearSession } from '@/lib/auth';
import { C } from '@/lib/constants';

interface Props {
  rsvped: boolean;
}

export default function TopNav({ rsvped }: Props) {
  const pathname = usePathname();
  const router = useRouter();

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
