export const STORAGE_KEY = 'rio27_guest';

export interface GuestSession {
  code: string;
  name: string;
  rsvped?: boolean;
  isAdmin?: boolean;
}

export function getSession(): GuestSession | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setSession(session: GuestSession) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}
