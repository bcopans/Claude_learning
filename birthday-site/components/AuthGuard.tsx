'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getSession, GuestSession } from '@/lib/auth';

interface Props {
  children: (session: GuestSession) => React.ReactNode;
}

export default function AuthGuard({ children }: Props) {
  const router = useRouter();
  const [session, setSession] = useState<GuestSession | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const s = getSession();
    if (!s) {
      router.replace('/');
    } else {
      setSession(s);
      setChecking(false);
    }
  }, [router]);

  if (checking || !session) return null;
  return <>{children(session)}</>;
}
