# App Shell Layout — Full Implementation


## File Structure

```
src/
  components/
    AppShell.tsx       ← single source of truth for navigation chrome
    TopNav.tsx         ← compatibility shim returning null (keep for old imports)
  app/
    layout.tsx         ← wraps children with <AppShell>
    page.tsx           ← homepage; does NOT render <TopNav />
    login/page.tsx     ← AppShell detects pathname='/login' and renders bare children
    profil/page.tsx    ← /profil page for self-service (used by AuthMenu dropdown)
```

## app/layout.tsx

```tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import AppShell from '@/components/AppShell';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'My App',
  description: '...',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" className={inter.variable}>
      <body className="bg-[#FAFAF9] text-slate-900 min-h-screen">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
```

## components/AppShell.tsx (full ~270 lines)

```tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';
import {
  LayoutDashboard, FlaskConical, ListPlus, History,
  Settings2, LogIn, LogOut, Menu, X, Beaker, UserCircle,
  ChevronDown,
  type LucideIcon,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase';
import type { Profile } from '@/types';

const publicLinks = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/bahan', label: 'Daftar Bahan', icon: FlaskConical },
];

const siswaLinks = [
  { href: '/pakai', label: 'Pakai Bahan', icon: ListPlus },
  { href: '/riwayat', label: 'Riwayat', icon: History },
  { href: '/profil', label: 'Profil Saya', icon: UserCircle },
];

const guruLinks = [
  { href: '/pakai', label: 'Pakai Bahan', icon: ListPlus },
  { href: '/riwayat', label: 'Riwayat', icon: History },
  { href: '/kelola-bahan', label: 'Kelola Bahan', icon: Beaker },
  { href: '/admin', label: 'Manajemen Akun', icon: Settings2 },
  { href: '/profil', label: 'Profil Saya', icon: UserCircle },
];

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    let mounted = true;
    const supabase = getSupabaseClient();

    async function loadProfile() {
      try {
        const accessToken = getCookie('sb-access-token');
        const refreshToken = getCookie('sb-refresh-token');

        // No tokens → guest user, skip auth check entirely
        if (!accessToken || !refreshToken) {
          if (mounted) setLoading(false);
          return;
        }

        await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        });

        const { data: { user } } = await supabase.auth.getUser();
        if (!user) { if (mounted) setLoading(false); return; }

        const { data } = await supabase
          .from('profiles').select('*').eq('id', user.id).single();

        if (mounted) {
          if (data) setProfile(data as Profile);
          setLoading(false);
        }
      } catch (err) {
        console.error('AppShell loadProfile error:', err);
        if (mounted) setLoading(false);
      }
    }

    loadProfile();
    return () => { mounted = false; };
  }, [pathname]);

  // Close mobile drawer on route change
  useEffect(() => { setDrawerOpen(false); }, [pathname]);

  async function handleLogout() {
    setLoggingOut(true);
    const supabase = getSupabaseClient();
    await supabase.auth.signOut();
    document.cookie = 'sb-access-token=; path=/; max-age=0';
    document.cookie = 'sb-refresh-token=; path=/; max-age=0';
    window.location.href = '/';
  }

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(href + '/');

  const links = profile?.role === 'guru'
    ? [...publicLinks, ...guruLinks]
    : profile?.role === 'siswa'
      ? [...publicLinks, ...siswaLinks]
      : publicLinks;

  // Login page: render bare children (no shell)
  if (pathname === '/login') return <>{children}</>;

  return (
    <div className="min-h-screen">
      {/* DESKTOP SIDEBAR (lg+) — navigation only */}
      <aside className="hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:border-r lg:border-slate-200 lg:bg-white">
        <SidebarContent links={links} isActive={isActive} />
      </aside>

      {/* TOP BAR — visible on all sizes, offset right of sidebar on desktop */}
      <header className="sticky top-0 z-40 bg-white/85 backdrop-blur-md border-b border-slate-200 lg:ml-64">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-3">
            {/* LEFT: hamburger + brand (mobile only) */}
            <div className="flex items-center gap-2 shrink-0 lg:hidden">
              <button
                onClick={() => setDrawerOpen(true)}
                className="p-2 -ml-1 rounded-lg text-slate-700 hover:bg-slate-100"
                aria-label="Buka menu"
              >
                <Menu size={20} />
              </button>
              <Link href="/" className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-600 to-teal-800 flex items-center justify-center shadow-sm">
                  <FlaskConical className="w-5 h-5 text-white" strokeWidth={2.2} />
                </div>
                <div className="hidden sm:block leading-tight">
                  <div className="text-sm font-bold text-slate-900">Inventaris Lab</div>
                </div>
              </Link>
            </div>

            {/* Desktop spacer (sidebar handles the left edge) */}
            <div className="hidden lg:block flex-1" />

            {/* RIGHT: auth menu — same on all sizes */}
            <div className="shrink-0">
              <AuthMenu
                profile={profile}
                loading={loading}
                loggingOut={loggingOut}
                onLogout={handleLogout}
              />
            </div>
          </div>
        </div>
      </header>

      {/* MOBILE DRAWER (overlay sidebar) */}
      {drawerOpen && (
        <>
          <div
            onClick={() => setDrawerOpen(false)}
            className="lg:hidden fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm"
          />
          <aside className="lg:hidden fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-slate-200 shadow-xl flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <Link href="/" onClick={() => setDrawerOpen(false)} className="flex items-center gap-2.5">
                {/* brand */}
              </Link>
              <button onClick={() => setDrawerOpen(false)} aria-label="Tutup menu">
                <X size={18} />
              </button>
            </div>
            <SidebarContent links={links} isActive={isActive} hideHeader />
          </aside>
        </>
      )}

      {/* MAIN CONTENT */}
      <main className="lg:ml-64 min-w-0">
        {children}
      </main>
    </div>
  );
}

function SidebarContent({
  links, isActive, hideHeader,
}: {
  links: Array<{ href: string; label: string; icon: LucideIcon }>;
  isActive: (href: string) => boolean;
  hideHeader?: boolean;
}) {
  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {!hideHeader && (
        <div className="p-5 border-b border-slate-200">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-600 to-teal-800 flex items-center justify-center shadow-sm">
              <FlaskConical className="w-5 h-5 text-white" strokeWidth={2.2} />
            </div>
            <div className="leading-tight min-w-0">
              <div className="text-sm font-bold text-slate-900 truncate">Inventaris Lab</div>
            </div>
          </Link>
        </div>
      )}

      <nav className="flex-1 p-3 flex flex-col gap-0.5">
        <div className="px-3 pt-2 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Menu
        </div>
        {links.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                active
                  ? 'bg-teal-50 text-teal-700 shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <Icon size={17} strokeWidth={2.2} className={active ? 'text-teal-700' : 'text-slate-500'} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

function AuthMenu({
  profile, loading, loggingOut, onLogout,
}: {
  profile: Profile | null;
  loading: boolean;
  loggingOut: boolean;
  onLogout: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) { if (e.key === 'Escape') setOpen(false); }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open]);

  if (loading) return <div className="w-9 h-9 rounded-full bg-slate-100 animate-pulse" />;

  if (!profile) {
    return (
      <Link href="/login" className="btn btn-primary !py-1.5 !px-3 text-[13px]">
        <LogIn size={14} strokeWidth={2.2} />
        Masuk
      </Link>
    );
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-2 p-1 pr-2 sm:pr-3 rounded-full hover:bg-slate-100 transition-colors ${open ? 'bg-slate-100' : ''}`}
        aria-label="Menu akun"
        aria-expanded={open}
      >
        <Avatar profile={profile} />
        <div className="hidden sm:block text-left leading-tight max-w-[140px]">
          <div className="text-sm font-semibold text-slate-900 truncate">{profile.nama}</div>
          <div className="text-[11px] text-slate-500 capitalize truncate">
            {profile.role}{profile.kelas ? ` · ${profile.kelas}` : ''}
          </div>
        </div>
        <ChevronDown size={14} className={`hidden sm:block text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-64 rounded-xl bg-white border border-slate-200 shadow-lg overflow-hidden z-50">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-3">
            <Avatar profile={profile} />
            <div className="leading-tight min-w-0 flex-1">
              <div className="text-sm font-semibold text-slate-900 truncate">{profile.nama}</div>
              <div className="text-xs text-slate-500 truncate">
                {profile.email || `${profile.role}${profile.kelas ? ` · ${profile.kelas}` : ''}`}
              </div>
            </div>
          </div>

          <div className="p-1.5">
            <Link
              href="/profil"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <UserCircle size={16} strokeWidth={2.2} className="text-slate-500" />
              Profil Saya
            </Link>
            <button
              onClick={() => { setOpen(false); onLogout(); }}
              disabled={loggingOut}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              <LogOut size={16} strokeWidth={2.2} />
              {loggingOut ? 'Keluar...' : 'Keluar'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Avatar({ profile }: { profile: Profile }) {
  return (
    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-sm shrink-0 ${
      profile.role === 'guru'
        ? 'bg-gradient-to-br from-amber-500 to-amber-700'
        : 'bg-gradient-to-br from-teal-500 to-teal-700'
    }`}>
      {profile.nama.charAt(0).toUpperCase()}
    </div>
  );
}
```

## Verification (DOM probes via browser_console)

After deploy, use these DOM probes to confirm layout — much faster than vision:

```js
// 1. Sidebar present + offset correct (desktop)
({
  viewportWidth: window.innerWidth,
  sidebar: (() => {
    const a = document.querySelector('aside');
    const r = a?.getBoundingClientRect();
    return r ? { left: r.left, width: r.width, visible: r.width > 0 } : 'not found';
  })(),
  main: (() => {
    const m = document.querySelector('body > div > main');
    const r = m?.getBoundingClientRect();
    return r ? { left: r.left } : 'not found';
  })(),
  links: Array.from(document.querySelectorAll('aside nav a')).map(a => a.textContent.trim()),
})
// Expected: sidebar.left=0, width=256, main.left=256
```

```js
// 2. AuthMenu state — guest vs logged in
({
  loginBtn: !!document.querySelector('header a[href="/login"]'),
  authMenuBtn: !!document.querySelector('header [aria-label="Menu akun"]'),
  loadingPulse: !!document.querySelector('header .animate-pulse'),
})
// Guest: loginBtn=true, authMenuBtn=false
// Logged in: loginBtn=false, authMenuBtn=true
```

```js
// 3. Active state highlights correct nav link
Array.from(document.querySelectorAll('aside nav a')).map(a => ({
  label: a.textContent.trim(),
  active: a.classList.contains('bg-teal-50')
}))
// Expected: exactly one link has active=true matching pathname
```

```js
// 4. Sidebar must NOT contain logout button (logout lives in AuthMenu only)
({
  sidebarHasLogout: !!document.querySelector('aside button'),
  sidebarHasKeluar: Array.from(document.querySelectorAll('aside *')).filter(el => el.textContent.toLowerCase().includes('keluar')).length,
})
// Expected: both 0/false. If non-zero, the user will complain "tombol keluar di hamburger ga perlu, cukup di kanan atas".
```

## Iteration history (why this layout, not earlier alternatives)

User went through these stages before settling. Each was wrong because:

1. **Centered title TopNav** — title "Inventaris Pengawasan Mutu Hasil Pertanian" was 35+ chars, overlapped hamburger and avatar at tablet width.
2. **Hamburger-only at all sizes** — "kalo bisa pada saat mode desktop tampilannya full itu langsung saja ga perlu ada hamburger". Drawer felt heavy on desktop where there was room for inline nav.
3. **Inline horizontal nav at desktop, hamburger at mobile** — too cramped with 7 links, label truncation looked unprofessional.
4. **Hamburger drawer with 3-column grid menu at desktop** — "tampilannya malah ke samping bukan ke bawah kayak di hp... jangan disimpan di tengah gitu acak acakan". Discoverability worse than persistent sidebar.
5. **Sidebar with logout in sidebar footer** — "untuk tombol masuknya tetep simpan di kanan atas aja, dan setelah login juga kalo klik profil sebelah kanan itu ada tombol keluar. jadi di menu hamburger ga perlu ada".

Final layout (this one) addresses all five corrections at once. Ship it from day one to skip the rebuild cycle.
