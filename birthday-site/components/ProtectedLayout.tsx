'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getSession } from '@/lib/auth';
import TopNav from './TopNav';
import { C } from '@/lib/constants';

export interface SessionWithRsvp {
  code: string;
  name: string;
  rsvped: boolean;
  isAdmin: boolean;
}

interface Props {
  children: (session: SessionWithRsvp, onRsvped: () => void) => React.ReactNode;
}

export default function ProtectedLayout({ children }: Props) {
  const router = useRouter();
  const [session, setSession] = useState<SessionWithRsvp | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const s = getSession();
    if (!s) {
      router.replace('/');
      return;
    }

    const isAdmin = !!s.isAdmin;
    const rsvpCache = localStorage.getItem(`rio27_rsvped_${s.code}`);
    if (rsvpCache === 'yes') {
      setSession({ code: s.code, name: s.name, rsvped: true, isAdmin });
      setChecking(false);
    } else {
      setSession({ code: s.code, name: s.name, rsvped: false, isAdmin });
      setChecking(false);
      // Async background check to update rsvped status
      fetch(`/api/rsvp?code=${s.code}`)
        .then((r) => r.json())
        .then(({ rsvp }) => {
          if (rsvp?.attending === 'yes') {
            localStorage.setItem(`rio27_rsvped_${s.code}`, 'yes');
            setSession((prev) => prev ? { ...prev, rsvped: true } : prev);
          }
        })
        .catch(() => {});
    }
  }, [router]);

  if (checking || !session) {
    return (
      <div
        style={{
          minHeight: '100vh',
          background: C.greenDeep,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      />
    );
  }

  const handleRsvped = () => {
    if (!session) return;
    localStorage.setItem(`rio27_rsvped_${session.code}`, 'yes');
    setSession((prev) => prev ? { ...prev, rsvped: true } : prev);
  };

  return (
    <div style={{ fontFamily: "'Space Grotesk', system-ui, sans-serif", background: C.cream, minHeight: '100vh' }}>
      <TopNav rsvped={session.rsvped} isAdmin={session.isAdmin} />
      {children(session, handleRsvped)}
    </div>
  );
}
