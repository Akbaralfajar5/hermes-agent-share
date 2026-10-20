---
name: nextjs-supabase-deployment
description: "Deploy Next.js apps with Supabase auth + realtime — schema setup, auth triggers, service role API routes, and Vercel env vars. Covers common pitfalls: trigger errors, RLS, cookie-based auth in API routes."
tags: [nextjs, supabase, auth, deployment, vercel, realtime, rls, service-role]
---

# Next.js + Supabase Deployment

Full workflow for building and deploying Next.js apps backed by Supabase (auth, database, realtime).

## Stack

- Next.js 14 App Router
- `@supabase/supabase-js` (NOT `@supabase/ssr` — causes type conflicts with @types/react v18)
- Supabase Auth + Postgres + Realtime
- Vercel deployment

## ⚠️ Do NOT use `@supabase/ssr`

`@supabase/ssr` causes type conflicts with `@types/react` v18 and Next.js 14. Use `@supabase/supabase-js` directly with manual cookie handling in middleware.

## Auth Architecture

Split auth into two files to avoid `next/headers` in client components:

**`src/lib/auth-server.ts`** — server-only (getSession, getUser, getServerProfile)
```ts
import { cookies } from 'next/headers'  // server only
import { createClient } from '@supabase/supabase-js'

export function createServerSupabaseClient() {
  const cookieStore = cookies()
  const token = cookieStore.get('sb-access-token')?.value
  const client = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
  // set auth header manually if token exists
  return client
}

export async function getServerProfile(): Promise<Profile | null> { ... }
```

**`src/lib/auth-client.ts`** — client-only (signIn, signOut, signUp)
```ts
'use client'
import { createClient } from '@supabase/supabase-js'
// no next/headers here
```

## API Routes: Auth via Cookie

API routes cannot use `next/headers` the same way. Read the JWT from cookies directly:

```ts
// In any API route handler
async function getCallerProfile(request: NextRequest) {
  const token = request.cookies.get('sb-access-token')?.value
  if (!token) return null

  const adminClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )

  const { data: { user }, error } = await adminClient.auth.getUser(token)
  if (error || !user) return null

  const { data: profile } = await adminClient
    .from('profiles')
    .select('id, role')
    .eq('id', user.id)
    .single()

  return profile
}
```

## Service Role Key

For admin operations (create user, delete user, bypass RLS):

```ts
const adminClient = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)
```

**Env vars needed:**
- `NEXT_PUBLIC_SUPABASE_URL` — public, safe to expose
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — public anon key
- `SUPABASE_SERVICE_ROLE_KEY` — server-only, never expose to client

Set via Vercel CLI:
```bash
cd ~/your-project
npx vercel env add NEXT_PUBLIC_SUPABASE_URL production --token <TOKEN> <<< "https://xxx.supabase.co"
npx vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production --token <TOKEN> <<< "eyJ..."
npx vercel env add SUPABASE_SERVICE_ROLE_KEY production --token <TOKEN> <<< "eyJ..."
```

## SQL Schema Pattern

```sql
-- profiles table (mirrors auth.users)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  nama TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  kelas TEXT,
  role TEXT NOT NULL DEFAULT 'siswa' CHECK (role IN ('siswa', 'guru')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Service role full access" ON profiles USING (true) WITH CHECK (true);
```

## ⚠️ Critical: Auth Trigger for New Users

**"Database error creating new user"** in Supabase dashboard = trigger missing or broken.

When a user is created via `auth.admin.createUser()` or the dashboard, Supabase fires `on_auth_user_created` trigger to insert into `profiles`. If this trigger is missing or fails, user creation fails entirely.

**Fix — run in SQL Editor:**
```sql
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, nama, email, role)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'nama', split_part(NEW.email, '@', 1)),
    NEW.email,
    'siswa'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

Key points:
- `SECURITY DEFINER` — runs as table owner, bypasses RLS
- `ON CONFLICT (id) DO NOTHING` — safe to re-run
- `COALESCE(raw_user_meta_data->>'nama', split_part(email, '@', 1))` — fallback nama from email prefix
- After fixing trigger, set guru role manually: `UPDATE profiles SET role = 'guru' WHERE email = '...';`

## Create User via Service Role (Admin Panel)

Guru buat akun siswa dari dalam website — tidak perlu akses Supabase dashboard:

```ts
// POST /api/admin/create-user
const { data: newUser, error } = await adminClient.auth.admin.createUser({
  email,
  password,
  email_confirm: true,  // skip email verification
  user_metadata: { nama, kelas }
})

// ⚠️ Use UPSERT, not INSERT — the on_auth_user_created trigger may have
// already inserted the profile row. INSERT will fail with:
//   "duplicate key value violates unique constraint profiles_pkey"
await adminClient.from('profiles').upsert({
  id: newUser.user.id,
  nama, email,
  kelas: role === 'siswa' ? kelas : null,
  role,
}, { onConflict: 'id' })
```

This is critical: even if you "know" the trigger isn't there, `upsert` is the safe default. Future schema changes that add the trigger won't break the API.

### Multi-role Admin Panel (cascading admin rights)

When ALL guru can create accounts (not just one super-admin), the API shape:

```ts
const DEFAULT_PASSWORD = '123456'

export async function POST(request: NextRequest) {
  const profile = await getCallerProfile(request)
  if (!profile) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (profile.role !== 'guru') {
    return NextResponse.json({ error: 'Hanya guru yang bisa membuat akun' }, { status: 403 })
  }

  const { nama, email, password, kelas, role } = await request.json()
  if (!nama || !email) return NextResponse.json({ error: '...' }, { status: 400 })

  // Validate role — never trust client
  const newUserRole = role === 'guru' ? 'guru' : 'siswa'
  if (newUserRole === 'siswa' && !kelas) {
    return NextResponse.json({ error: 'Kelas wajib untuk siswa' }, { status: 400 })
  }

  // Default password fallback
  const finalPassword = password && password.length >= 6 ? password : DEFAULT_PASSWORD
  const usedDefault = !password || password.length < 6

  // ... create + upsert profile ...

  // Return password in response so admin UI can show it for sharing
  return NextResponse.json({
    success: true,
    user: { id, nama, email, kelas, role: newUserRole },
    password: finalPassword,
    usedDefault,
  })
}
```

Key UX points:
- Return the password (default or custom) in the response so the admin can copy/share — they won't see it again
- `usedDefault` flag lets the UI nudge users to change their password
- Admin UI should have role toggle (button group, not dropdown — clearer affordance) and password mode toggle (Default / Custom)
- Self-protection in UI: don't show "Hapus" button for the caller's own row (`isSelf = user.id === callerId`)
- Filter tabs (Semua / Guru / Siswa) make a long list manageable

## Self-Service Change Password (Verified by Re-Auth)

For "user changes own password" flows, you cannot use the admin client alone — you must verify the user's *current* password before allowing the change. Otherwise a stolen JWT can permanently lock out the real owner.

Pattern: re-authenticate via anon client with the supplied current password, then update via admin client. This proves possession of the existing password.

```ts
// /api/profile/change-password/route.ts
export async function POST(request: NextRequest) {
  const accessToken = request.cookies.get('sb-access-token')?.value
  if (!accessToken) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const adminClient = getAdminClient()
  const { data: { user }, error: tokenErr } = await adminClient.auth.getUser(accessToken)
  if (tokenErr || !user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { currentPassword, newPassword } = await request.json()
  if (!newPassword || newPassword.length < 6) {
    return NextResponse.json({ error: 'Password baru minimal 6 karakter' }, { status: 400 })
  }
  if (!currentPassword) {
    return NextResponse.json({ error: 'Password saat ini wajib diisi' }, { status: 400 })
  }

  // Re-auth check — confirms caller knows current password
  const anonClient = createClient(SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
  const { error: signInErr } = await anonClient.auth.signInWithPassword({
    email: user.email!,
    password: currentPassword,
  })
  if (signInErr) {
    return NextResponse.json({ error: 'Password saat ini salah' }, { status: 400 })
  }

  // Update password via admin client
  const { error: updateErr } = await adminClient.auth.admin.updateUserById(user.id, {
    password: newPassword,
  })
  if (updateErr) return NextResponse.json({ error: updateErr.message }, { status: 500 })

  // ⚠️ Supabase invalidates the existing session after password change.
  // Re-sign-in with the new password and rotate the cookies, or the user
  // gets booted to login on next request.
  const { data: refreshData } = await anonClient.auth.signInWithPassword({
    email: user.email!,
    password: newPassword,
  })

  const response = NextResponse.json({ success: true })
  if (refreshData?.session) {
    const maxAge = refreshData.session.expires_in || 3600
    response.cookies.set('sb-access-token', refreshData.session.access_token, {
      path: '/', maxAge, sameSite: 'lax',
    })
    response.cookies.set('sb-refresh-token', refreshData.session.refresh_token, {
      path: '/', maxAge: 60 * 60 * 24 * 30, sameSite: 'lax',
    })
  }
  return response
}
```

**Why all three steps matter:**
1. **Verify token** → caller is currently logged in
2. **Re-auth with currentPassword** → caller knows the current password (token alone isn't enough; a leaked JWT must not let an attacker change the password)
3. **Rotate cookies after update** → without this, every subsequent request from the user 401s because Supabase invalidated the old session token. Symptom: form says "success" but the next API call (e.g. delete a record) fails 401.

Client-side validation in the form (additional defenses, not replacements):
- `newPassword !== confirmPassword` → "Konfirmasi tidak cocok"
- `newPassword === currentPassword` → "Password baru tidak boleh sama"
- `newPassword.length < 6` → block submit

## Rate-Limit Login Attempts (Lockout) Without DDL

When you can't run migrations on Supabase (e.g. service role key encrypted in Vercel, no SQL Editor access from automation), you can still implement login lockout by storing per-user state in `auth.users.app_metadata` JSON. Updateable via the admin client, persistent cross-instance, and the anon client cannot write it — so it can't be tampered with from the browser.

**Storage shape (no migration needed):**
```ts
auth.users.app_metadata = {
  failed_attempts: number,        // consecutive fails
  locked_until: string | null,    // ISO timestamp when lockout expires
}
```

**Why this pattern:**
- **No DDL needed** — `app_metadata` exists on every user. No new table, no migration.
- **Tamper-proof** — only service role can write `app_metadata`. Anon-key clients (browser) cannot modify it even with a valid session JWT.
- **Cross-instance persistent** — Vercel serverless instances don't share memory, but all read/write the same Postgres user row.
- **Reject correct password during lockout** — check lockout BEFORE `signInWithPassword`. Even a correct password should be rejected while locked. Putting the check in the failure branch creates a bypass.

**Custom login route — replaces direct client `signInWithPassword`:**
```ts
// /api/auth/login/route.ts
const MAX_ATTEMPTS = 5
const LOCKOUT_MINUTES = 15

export async function POST(req: NextRequest) {
  const { email, password } = await req.json()
  const admin = getAdminClient()

  // 1. Look up user by email (listUsers is OK for small apps; for >1k users
  //    maintain email→id in profiles and query that)
  const { data: usersList } = await admin.auth.admin.listUsers()
  const user = usersList.users.find(u => u.email === email)

  // 2. Check lockout BEFORE auth attempt
  if (user) {
    const meta = (user.app_metadata || {}) as { failed_attempts?: number; locked_until?: string }
    if (meta.locked_until && new Date(meta.locked_until) > new Date()) {
      const secondsLeft = Math.ceil((new Date(meta.locked_until).getTime() - Date.now()) / 1000)
      return NextResponse.json({ error: 'Akun terkunci sementara', locked: true, secondsLeft }, { status: 429 })
    }
  }

  // 3. Verify password via anon client (admin auth bypasses password check, can't use it)
  const anon = createClient(SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
  const { data: signInData, error: signInError } = await anon.auth.signInWithPassword({ email, password })

  if (signInError || !signInData?.session) {
    if (user) {
      const next = ((user.app_metadata?.failed_attempts as number) || 0) + 1
      const newMeta: any = { ...user.app_metadata, failed_attempts: next }
      if (next >= MAX_ATTEMPTS) {
        newMeta.locked_until = new Date(Date.now() + LOCKOUT_MINUTES * 60_000).toISOString()
      }
      await admin.auth.admin.updateUserById(user.id, { app_metadata: newMeta })
      return NextResponse.json({
        error: 'Email atau password salah',
        remainingAttempts: Math.max(0, MAX_ATTEMPTS - next),
        ...(next >= MAX_ATTEMPTS ? { locked: true, secondsLeft: LOCKOUT_MINUTES * 60 } : {}),
      }, { status: 401 })
    }
    return NextResponse.json({ error: 'Email atau password salah' }, { status: 401 })
  }

  // 4. Success — reset counter, set cookies (same as normal signIn flow)
  await admin.auth.admin.updateUserById(user!.id, {
    app_metadata: { ...user!.app_metadata, failed_attempts: 0, locked_until: null },
  })
  const response = NextResponse.json({ success: true })
  response.cookies.set('sb-access-token', signInData.session.access_token, {
    path: '/', maxAge: signInData.session.expires_in || 3600, sameSite: 'lax',
  })
  response.cookies.set('sb-refresh-token', signInData.session.refresh_token, {
    path: '/', maxAge: 60 * 60 * 24 * 30, sameSite: 'lax',
  })
  return response
}
```

**Admin reset endpoint** (so admin can unlock a user who got stuck):
```ts
// /api/admin/reset-lockout/route.ts — admin/guru-only
export async function POST(req: NextRequest) {
  const profile = await getCallerProfile(req)
  if (!profile || profile.role !== 'guru') {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }
  const { userId } = await req.json()
  const admin = getAdminClient()
  const { data: { user } } = await admin.auth.admin.getUserById(userId)
  if (!user) return NextResponse.json({ error: 'User not found' }, { status: 404 })
  await admin.auth.admin.updateUserById(userId, {
    app_metadata: { ...user.app_metadata, failed_attempts: 0, locked_until: null },
  })
  return NextResponse.json({ success: true })
}
```

**Login page UI essentials:**
- Live countdown `mm:ss` while `locked === true` (setInterval, decrement, clear when 0)
- Disable email/password inputs, eye toggle, AND submit button when locked (not just the button — a determined user can re-enable inputs in DevTools and submit; disabled button is the real gate, but disabling all inputs is clearer UX)
- Red banner "Akun Terkunci Sementara · Coba lagi dalam 14:32"
- When `remainingAttempts` is 1 or 2, show amber warning "Sisa percobaan: 2"
- On 429 response, set `locked = true` and `secondsLeft = data.secondsLeft || 900`

**Pitfalls:**
- Don't use admin client for `signInWithPassword` — admin auth doesn't verify passwords. Use anon client.
- Increments aren't fully atomic (two parallel failed requests can race), so worst case the threshold trips at 4 instead of 5. Acceptable for a security-by-friction control.
- Don't store the lockout state in memory or localStorage — both reset across deployments / instances / devices.
- The admin reset endpoint must verify caller's role server-side; never trust a client-supplied `role` claim.
- After lockout expires, no separate cleanup job needed — just compare `locked_until > now()` on next attempt; expired timestamps are treated as unlocked.

See `references/login-rate-limit.md` for full route handlers, login page with countdown, admin UI for reset, and end-to-end curl tests.

## Default Password Pattern for Onboarding

When admins onboard users in batches, force-typing 30 unique passwords is friction. Provide a "Default password" toggle that fills in a known shared value (e.g. `123456`):

```tsx
// Admin form
<button onClick={() => setForm({ ...form, useDefault: true, password: '' })}>
  Default ({DEFAULT_PASSWORD})
</button>
<button onClick={() => setForm({ ...form, useDefault: false })}>
  Custom
</button>

{form.useDefault && (
  <p className="text-xs text-slate-500">
    Sarankan pengguna untuk segera mengubah password setelah login pertama.
  </p>
)}
```

After creation, surface the password in a copyable card so admin can paste it into WhatsApp/email:

```tsx
{createdInfo && (
  <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
    <div className="font-mono text-xs space-y-1">
      <div>Nama: {createdInfo.nama}</div>
      <div>Email: {createdInfo.email}</div>
      <div>Password: {createdInfo.password}</div>
    </div>
    <button onClick={copyCredentials}>Salin Kredensial</button>
  </div>
)}
```

The `/profil` page (self-service change password) closes the loop: user logs in with default → immediately changes it → no shared-secret risk lingering.

## Public-Page Email Field on Profile Type

If `Profile` type was originally defined without `email` (because email lived only in `auth.users`), and a profile page now wants to display it, you'll get TS error:
```
Type error: Property 'email' does not exist on type 'Profile'.
```

Fix: add `email?: string` to the type AND ensure the `profiles` table has an `email` column populated by the trigger. The optional marker keeps existing code that doesn't select email working.

```ts
export interface Profile {
  id: string
  nama: string
  email?: string  // optional — selects depend on caller
  role: UserRole
  kelas: string | null
  created_at?: string
}
```

## Test API End-to-End from Python Before Declaring Done

When shipping new auth/admin API routes, write a quick Python script that exercises the full happy + sad path against the deployed URL. Catches issues that browser clicking misses (e.g. siswa hitting admin endpoint, expired session after password change).

```python
import requests, re
ANON = re.search(r'NEXT_PUBLIC_SUPABASE_ANON_KEY="([^"]+)"', open("/tmp/env.prod").read()).group(1)
SUPABASE_URL = "https://<ref>.supabase.co"
BASE = "https://<app>.vercel.app"

# 1. Login as admin
r = requests.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    headers={"apikey": ANON}, json={"email": "...", "password": "..."})
sess = r.json()
cookies = {"sb-access-token": sess["access_token"], "sb-refresh-token": sess["refresh_token"]}

# 2. Create user, login as new user, change password, re-login
# 3. Negative: wrong current password (expect 400), siswa creates user (expect 403), anon (expect 401)
# 4. Cleanup: delete test users
```

Pull production env vars first: `npx vercel env pull --environment=production --token <TOKEN> --yes /tmp/env.prod`. Note: `SUPABASE_SERVICE_ROLE_KEY` may come back empty if marked sensitive — use the anon key for the test (it's enough to login).

## App Shell Layout (Sidebar Left + Top Bar Auth Menu) — Preferred Pattern

For dashboard-style apps with multiple authenticated sections, this is the layout users consistently end up requesting after iterating on simpler patterns. **Build this from the start** rather than going through the "centered topnav → hamburger-only → sidebar" rebuild cycle.

**Layout spec (the rule of three):**
- **Left sidebar (desktop ≥1024px)** — navigation only, vertical list, top-to-bottom. NOT centered, NOT horizontal. Persistent across all routes.
- **Top bar** — auth controls always at right. Guest sees a "Masuk" button. Logged-in user sees avatar + name + chevron, click opens dropdown with profile link + logout button.
- **Mobile (<1024px)** — hamburger left + brand, auth menu right (same component as desktop). Hamburger opens drawer overlay (sidebar nav, NOT auth controls — those stay in the top bar).

**Why this pattern:**
- Auth menu at top-right is universal muscle memory (Notion, Linear, Vercel, GitHub, every SaaS). Users expect it there.
- Sidebar = "where do I go", top-right = "who am I / sign out". Two separate mental models, two separate UI regions. Don't mix them.
- Login/logout in a hamburger drawer is non-discoverable. Users complained: "untuk tombol masuknya tetep simpan di kanan atas aja, dan setelah login juga kalo klik profil sebelah kanan itu ada tombol keluar. jadi di menu hamburger ga perlu ada".
- Sidebar (vertical, fixed width 256px) scales to many menu items without overflow. Inline horizontal nav breaks at 5+ items.

**Implementation skeleton:**
```tsx
// src/components/AppShell.tsx — wraps all authenticated pages
'use client'
export default function AppShell({ children }) {
  const pathname = usePathname()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [drawerOpen, setDrawerOpen] = useState(false)

  // Login page: no shell
  if (pathname === '/login') return <>{children}</>

  return (
    <div className="min-h-screen">
      {/* Desktop sidebar — fixed left, w-64 */}
      <aside className="hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:border-r lg:border-slate-200 lg:bg-white">
        <SidebarContent links={links} isActive={isActive} />
      </aside>

      {/* Top bar — full width but offset right of sidebar on desktop */}
      <header className="sticky top-0 z-40 bg-white/85 backdrop-blur-md border-b border-slate-200 lg:ml-64">
        {/* Mobile: hamburger + brand on left */}
        {/* All sizes: AuthMenu on right */}
      </header>

      {/* Mobile drawer — only opens via hamburger, only on <lg */}
      {drawerOpen && <MobileDrawer />}

      {/* Main content — offset by sidebar width on desktop */}
      <main className="lg:ml-64 min-w-0">{children}</main>
    </div>
  )
}
```

Mount AppShell once in `app/layout.tsx` so navigation is consistent across all routes:
```tsx
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body><AppShell>{children}</AppShell></body>
    </html>
  )
}
```

This means individual pages should NOT render their own `<TopNav />`. If migrating from per-page TopNav, keep a `TopNav.tsx` shim that returns `null` so existing imports don't break:
```tsx
// Compatibility shim — navigation now lives in AppShell
export default function TopNav() { return null }
```

**AuthMenu dropdown pattern (avatar → menu):**
```tsx
function AuthMenu({ profile, loading, loggingOut, onLogout }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // Close on outside click + Escape
  useEffect(() => {
    if (!open) return
    function onClick(e) { if (!ref.current?.contains(e.target)) setOpen(false) }
    function onKey(e) { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('mousedown', onClick); document.removeEventListener('keydown', onKey) }
  }, [open])

  if (loading) return <div className="w-9 h-9 rounded-full bg-slate-100 animate-pulse" />
  if (!profile) return <Link href="/login" className="btn btn-primary">Masuk</Link>

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(!open)}>
        <Avatar profile={profile} />
        <span className="hidden sm:block">{profile.nama}</span>
        <ChevronDown className={open ? 'rotate-180' : ''} />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-2 w-64 rounded-xl bg-white border shadow-lg">
          <div className="px-4 py-3 border-b">{/* avatar + name + email */}</div>
          <Link href="/profil">Profil Saya</Link>
          <button onClick={onLogout}>Keluar</button>
        </div>
      )}
    </div>
  )
}
```

See `references/app-shell-layout.md` for the full AppShell.tsx (~270 lines) including SidebarContent, MobileDrawer, Avatar, and the loadProfile guard.

## ⚠️ AppShell loadProfile: anon getUser() Throws → Stuck Loading

When AppShell mounts on a public page (no cookies), `supabase.auth.setSession()` and `supabase.auth.getUser()` can throw or reject because anon JWT has no `sub` claim:
```
{"code":403,"error_code":"bad_jwt","msg":"invalid claim: missing sub claim"}
```

If this throws, `setLoading(false)` never runs and the AuthMenu shows a perpetual `animate-pulse` skeleton forever. Symptom: Masuk button never appears for guests.

**Fix — guard with try/catch AND short-circuit on missing cookies:**
```ts
async function loadProfile() {
  try {
    const accessToken = getCookie('sb-access-token')
    const refreshToken = getCookie('sb-refresh-token')

    // No tokens → guest, skip auth entirely (don't call setSession or getUser)
    if (!accessToken || !refreshToken) {
      if (mounted) setLoading(false)
      return
    }

    await supabase.auth.setSession({ access_token: accessToken, refresh_token: refreshToken })
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { if (mounted) setLoading(false); return }

    const { data } = await supabase.from('profiles').select('*').eq('id', user.id).single()
    if (mounted) { if (data) setProfile(data as Profile); setLoading(false) }
  } catch (err) {
    console.error('AppShell loadProfile error:', err)
    if (mounted) setLoading(false)  // ← critical: must run on error path too
  }
}
```

Both guards matter: the early-return avoids an unnecessary 403 round-trip; the try/catch handles edge cases (network blip, malformed cookie, Supabase upgrade quirk) without leaving the UI stuck.

## Lucide Icon Prop Typing

When passing lucide icons through props (e.g. nav link config arrays), use the official `LucideIcon` type rather than hand-rolling `React.ComponentType<{ size?: number; ... }>`:
```ts
import { type LucideIcon } from 'lucide-react'

const links: Array<{ href: string; label: string; icon: LucideIcon }> = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  // ...
]
```
The hand-rolled type is too narrow — lucide's component accepts `size: number | string`, so the narrow `number` version triggers `Type 'string | number | null | undefined' is not assignable to type 'number'` at build time.

## Hamburger-Only Nav Pattern (deprecated — use App Shell instead)

Earlier guidance suggested a single hamburger drawer for all viewports. This works but feels less polished than a proper sidebar at desktop. Prefer "App Shell Layout" above for new dashboard apps. The hamburger-only pattern below remains valid for content sites or single-action apps where there's no need for persistent navigation.

```tsx
<header>
  <div className="flex items-center justify-between h-16 gap-3">
    {/* LEFT: Hamburger + Brand */}
    <div className="flex items-center gap-2">
      <button onClick={() => setOpen(!open)} className="p-2 -ml-1 rounded-lg">
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>
      <Link href="/" className="flex items-center gap-2.5">
        <BrandIcon />
        <div className="hidden sm:block">{/* compact subtitle */}</div>
      </Link>
    </div>

    {/* CENTER: empty spacer */}
    <div className="flex-1" />

    {/* RIGHT: User area */}
    <div>{/* avatar / login button */}</div>
  </div>

  {/* Drawer — works on all sizes */}
  {open && (
    <div className="border-t bg-white shadow-lg">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0.5">
        {/* nav links — responsive grid */}
      </div>
    </div>
  )}
</header>
```

Auto-close drawer on route change (avoids stuck-open state):
```ts
useEffect(() => { setOpen(false) }, [pathname])
```

Avoid `tailwindcss-animate` classes (`animate-in slide-in-from-top-2`) unless the plugin is actually installed in `tailwind.config`. They silently render nothing if the plugin is missing.

See `references/admin-and-self-service-account-management.md` for full admin panel + profile page implementation.

## Realtime Setup

```sql
-- Enable realtime for a table
ALTER PUBLICATION supabase_realtime ADD TABLE bahan_kimia;
```

```ts
// Client-side subscription
const channel = supabase
  .channel('bahan-changes')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'bahan_kimia' },
    (payload) => { /* update state */ })
  .subscribe()

// Cleanup
return () => { supabase.removeChannel(channel) }
```

## Supabase Auth Settings (Post-Deploy)

After deploying to Vercel, update in Supabase dashboard:
- **Authentication > Settings > Site URL** → `https://your-app.vercel.app`
- **Authentication > Settings > Redirect URLs** → `https://your-app.vercel.app/**`

## Middleware (Cookie-based Session)

```ts
// middleware.ts — refresh session without @supabase/ssr
import { NextRequest, NextResponse } from 'next/server'

export async function middleware(request: NextRequest) {
  const response = NextResponse.next()
  // pass-through — session refresh handled client-side
  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

## Cookie-based Auth: signIn Must Write Cookies Manually

Supabase JS v2 stores session in `localStorage` by default — middleware cannot read it. After `signInWithPassword`, manually write tokens to cookies:

```ts
// src/lib/auth.ts — signIn function
export async function signIn(email: string, password: string) {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase.auth.signInWithPassword({ email, password })

  if (data?.session) {
    const maxAge = data.session.expires_in || 3600
    document.cookie = `sb-access-token=${data.session.access_token}; path=/; max-age=${maxAge}; SameSite=Lax`
    document.cookie = `sb-refresh-token=${data.session.refresh_token}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax`
  }

  return { data, error }
}

// signOut must also clear cookies
export async function signOut() {
  const supabase = getSupabaseClient()
  const { error } = await supabase.auth.signOut()
  document.cookie = 'sb-access-token=; path=/; max-age=0'
  document.cookie = 'sb-refresh-token=; path=/; max-age=0'
  return { error }
}
```

Without this, middleware always sees unauthenticated → redirect loop after login.

After setting cookies, use `window.location.href = '/dashboard'` (hard redirect), NOT `router.push()`. `router.push` is a client-side navigation that doesn't re-send cookies to the server — middleware won't see the new cookie until a full page load.

```ts
// login/page.tsx — after signIn
if (data?.session) {
  document.cookie = `sb-access-token=${data.session.access_token}; path=/; max-age=${data.session.expires_in}; SameSite=Lax`
  document.cookie = `sb-refresh-token=${data.session.refresh_token}; path=/; max-age=${60*60*24*30}; SameSite=Lax`
}
window.location.href = '/dashboard'  // hard redirect — NOT router.push()
```

## ⚠️ profiles Table: email Column

If `profiles` table was created without `email` column but trigger tries to insert it, user creation fails silently. Always include `email TEXT` in profiles schema. If missing, add it:

```sql
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email text;
```

## Vercel Prebuilt Deploy (Bypass npm Install)

When Vercel build environment crashes with `npm error Exit handler never called!` (npm bug, not a code issue), build locally and upload prebuilt output:

```bash
# Build locally with production target
npx vercel build --prod --token <TOKEN> --yes

# Deploy prebuilt output (skips npm install on Vercel)
npx vercel deploy --prebuilt --prod --token <TOKEN> --yes
```

This is the reliable fallback when CLI deploy keeps failing. Root cause of the npm crash: disk full on VPS → npm cache corrupted. Fix: `npm cache clean --force` first.

## Vercel: Connect GitHub Repo via API

```bash
# Get project ID
curl -s "https://api.vercel.com/v9/projects/<project-name>?teamId=<team>" \
  -H "Authorization: Bearer <TOKEN>" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id'))"

# Get GitHub repo ID
curl -s "https://api.github.com/repos/<owner>/<repo>" \
  -H "Authorization: token <PAT>" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id'))"

# Link repo to project
curl -s -X POST "https://api.vercel.com/v9/projects/<project-id>/link?teamId=<team>" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"github","repo":"<owner>/<repo>","repoId":<id>,"productionBranch":"master"}'

# Trigger deploy from GitHub
curl -s -X POST "https://api.vercel.com/v13/deployments?teamId=<team>" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"<project>","gitSource":{"type":"github","repoId":<id>,"ref":"master"},"target":"production"}'
```

## Create User via Supabase Admin API (curl)

When Supabase dashboard "Add user" fails, use the admin API directly:

```bash
curl -s -X POST "https://<ref>.supabase.co/auth/v1/admin/users" \
  -H "Authorization: Bearer <SERVICE_ROLE_KEY>" \
  -H "apikey: <SERVICE_ROLE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass","email_confirm":true,"user_metadata":{"nama":"Nama User"}}'
```

Then update role:
```bash
curl -s -X PATCH "https://<ref>.supabase.co/rest/v1/profiles?id=eq.<user-id>" \
  -H "Authorization: Bearer <SERVICE_ROLE_KEY>" \
  -H "apikey: <SERVICE_ROLE_KEY>" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '{"role":"guru"}'
```

## ⚠️ `vercel build --prod` vs `next build` — Critical Difference

`npx next build` builds the app but does NOT populate `.vercel/output/functions/`. New routes added after the initial project setup will be **missing from Vercel** even though they exist in `.next/server/app/`.

**Always use `vercel build --prod` for prebuilt deploys:**
```bash
# WRONG — new routes won't appear on Vercel
npx next build
npx vercel deploy --prebuilt --prod --token <TOKEN> --yes

# CORRECT — populates .vercel/output/functions/ with all routes
npx vercel build --prod --token <TOKEN>
npx vercel deploy --prebuilt --prod --token <TOKEN> --yes
```

Symptom: page returns 404 on Vercel but exists locally. Check:
```bash
ls .vercel/output/functions/ | grep <route-name>
# If missing → used next build instead of vercel build
```

## ⚠️ Vercel Encrypted Env Vars Cannot Be Decrypted via API

`sensitive` type env vars (set via Vercel dashboard or CLI) return `decrypted: false` even with `?decrypt=true` query param. The Vercel API does not expose plaintext values for sensitive vars.

```bash
# This returns decrypted: false for sensitive vars
curl "https://api.vercel.com/v9/projects/<id>/env/<env-id>?decrypt=true" \
  -H "Authorization: Bearer <TOKEN>"
# → {"type":"sensitive","decrypted":false,...}
```

**Workaround for running SQL migrations when you can't access the service key locally:**
- Option A: Run SQL directly in Supabase dashboard SQL Editor
- Option B: Create a temporary API route that runs the migration on first request, then delete it
- Option C: `vercel env pull --environment production` — but sensitive vars come back as empty strings

## ⚠️ Supabase Schema Cache Error After Adding Column

After adding a column to a table (`ALTER TABLE ... ADD COLUMN`), if the API route still sends that column in INSERT/UPDATE payloads before Supabase refreshes its schema cache, you get:
```
{"error": "Could not find the 'deskripsi' column of 'bahan_kimia' in the schema cache"}
```

Two fixes:
1. **Wait** — Supabase schema cache refreshes within ~30 seconds
2. **Remove the field from the payload** until the migration is confirmed applied

If the column doesn't exist yet and you can't run the migration immediately, remove the field from the API route entirely rather than letting it fail at runtime.

## ⚠️ createClient Must Be Inside Handler, Not Module Level

Calling `createClient(url, process.env.SERVICE_ROLE_KEY!)` at module level causes build-time crash:
```
Error: supabaseKey is required.
Failed to collect page data for /api/your-route
```

This happens because `process.env.SERVICE_ROLE_KEY` is `undefined` at build time (server-only env vars are not inlined). The client is instantiated during module evaluation, before any request arrives.

**Wrong:**
```ts
// top of file — crashes at build time
const supabaseAdmin = createClient(URL, process.env.SUPABASE_SERVICE_ROLE_KEY!)

export async function GET() {
  const { data } = await supabaseAdmin.from('table').select()
  ...
}
```

**Correct — wrap in a factory function:**
```ts
function getAdminClient() {
  return createClient(SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

export async function GET() {
  const supabase = getAdminClient()  // called at request time, env var is available
  const { data } = await supabase.from('table').select()
  ...
}
```

This applies to any server-only env var (`SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, etc.) used in API routes.

## ⚠️ NEXT_PUBLIC env vars: Always Use Fallback

`NEXT_PUBLIC_*` vars are inlined at build time. If the build runs without them set (e.g. prebuilt deploy where env vars were added after build), the client bundle gets `undefined`. **Always add a hardcoded fallback** in `supabase.ts`:

```ts
// WRONG — silently undefined if env var missing at build time
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!

// CORRECT — fallback ensures client always has a working URL
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://yourref.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJ...'
```

The anon key is safe to hardcode (it's public). The service role key is NOT — keep that server-only via env var only.

## ⚠️ Supabase JS v2 Latest: WebSocket Crash on Node 20

`@supabase/supabase-js` versions newer than `2.39.8` crash on Node.js 20 with:
```
Error: Node.js 20 detected without native WebSocket support.
```
This causes **500 on every server-rendered page**. Fix: pin to safe version:
```bash
npm install @supabase/supabase-js@2.39.8
```

## ⚠️ Client-Side Session Lost When localStorage Cleared (Cookie Still Valid)

Symptom: User logs in successfully, navigates between pages, suddenly TopNav/Sidebar shows "Masuk" again as if logged out — but cookie is still set and middleware doesn't redirect to login. `localStorage` got cleared (browser quirk, hard refresh in some browsers, or new tab in incognito) but cookies persisted.

`@supabase/supabase-js` v2 stores session in `localStorage` only. When localStorage is empty, `supabase.auth.getUser()` returns `null` even though the JWT in cookie is still valid. Server-rendered pages still see the user (cookie-based) but client components don't.

**Fix — restore session from cookie at component mount:**

```ts
'use client'
useEffect(() => {
  const supabase = getSupabaseClient()

  async function loadProfile() {
    // Recover session from cookie if localStorage was cleared
    const accessToken = getCookie('sb-access-token')
    const refreshToken = getCookie('sb-refresh-token')
    if (accessToken && refreshToken) {
      await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      })
    }

    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return
    // ... fetch profile
  }
  loadProfile()
}, [])

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}
```

Apply this pattern to: TopNav/Sidebar, every protected client page that does role checks (`/admin`, `/kelola-bahan`, etc.), and any client component that calls `supabase.from(...).insert()` or `update()` directly.

**Better alternative for mutations:** Don't rely on client-side authenticated Supabase calls at all. POST to a server-side API route that reads `sb-access-token` from cookies and uses service role to perform the action. See "Mutate via Server API, Not Client" below.

## Mutate via Server API, Not Client (Recommended Pattern)

Anti-pattern: client component does `supabase.from('pemakaian').insert(...)` — fails silently if localStorage was cleared, requires RLS policies for every operation, can't enforce business rules cleanly.

Better pattern: client POSTs to `/api/<resource>`, server verifies caller via cookie + service role, performs the mutation:

```ts
// /api/pemakaian/route.ts
export async function POST(req: NextRequest) {
  const supabase = getAdminClient()
  const accessToken = req.cookies.get('sb-access-token')?.value
  if (!accessToken) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data: { user }, error } = await supabase.auth.getUser(accessToken)
  if (error || !user) return NextResponse.json({ error: 'Invalid session' }, { status: 401 })

  // Now do the mutation with service role + verified user.id
  const body = await req.json()
  // ... insert with user_id: user.id
}
```

Benefits: works regardless of client-side session state, enforces business rules (stock check, etc.) server-side, no need for complex RLS for every mutation type.

**Client form pairing with server API:**
```ts
'use client'
async function handleSubmit(e: React.FormEvent) {
  e.preventDefault()
  setLoading(true)

  try {
    const res = await fetch('/api/pemakaian', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',  // ⚠️ required so cookies are sent
      body: JSON.stringify({ bahan_id, jumlah, keterangan }),
    })

    const result = await res.json()
    if (!res.ok) {
      setError(result.error || 'Gagal menyimpan')
      setLoading(false)
      return
    }

    setSuccess('Berhasil')
    router.refresh()  // re-fetch server components (riwayat, dashboard stok)
  } catch {
    setError('Gagal terhubung ke server')
  } finally {
    setLoading(false)
  }
}
```

Key points:
- `credentials: 'include'` — without it, cookies don't reach the API route on cross-origin or even some same-origin Vercel setups
- `router.refresh()` after success to re-render server components (so dashboard stock count updates immediately)
- Form-side validation is duplicated server-side in the API route — never trust client validation alone

**Browser automation testing tip:** When testing a controlled-input form via `browser_console`, setting `select.value` and dispatching `change` event often does NOT propagate to React state. Use `form.requestSubmit()` after setting values, OR use the React-native input setter:
```js
const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set
setter.call(selectEl, newValue)
selectEl.dispatchEvent(new Event('change', { bubbles: true }))
```

## Public Homepage + Login-Gated Areas Pattern

For apps where the homepage and read-only pages should be public (no login required) but mutations/admin are gated:

**1. Middleware whitelist instead of blacklist:**
```ts
// middleware.ts
const PROTECTED_ROUTES = ['/kelola-bahan', '/admin', '/pakai', '/riwayat']

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  if (pathname.startsWith('/_next') || pathname.startsWith('/api') || pathname.includes('.')) {
    return NextResponse.next()
  }
  const accessToken = request.cookies.get('sb-access-token')?.value
  const isProtected = PROTECTED_ROUTES.some((r) => pathname === r || pathname.startsWith(r + '/'))
  if (isProtected && !accessToken) {
    const url = new URL('/login', request.url)
    url.searchParams.set('redirect', pathname)  // remember where user wanted to go
    return NextResponse.redirect(url)
  }
  if (accessToken && pathname === '/login') {
    return NextResponse.redirect(new URL('/', request.url))
  }
  return NextResponse.next()
}
```

**2. Public pages use service role on server (RLS bypass):**
```ts
// app/page.tsx — public homepage
function getPublicClient() {
  return createClient(SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

export default async function HomePage() {
  const supabase = getPublicClient()
  const { data } = await supabase.from('bahan_kimia').select('*')
  // ... render publicly
}
```
Why: anon key is blocked by RLS by default. Service role bypasses RLS. Safe to use server-side because the key is never sent to the client.

**3. Login page reads `?redirect=` and sends user back:**
```ts
const searchParams = useSearchParams()
const redirectTo = searchParams.get('redirect') || '/'
// after successful signIn:
window.location.href = redirectTo
```

**4. Realtime in client only when authenticated:**
```ts
useEffect(() => {
  const supabase = getSupabaseClient()
  let channel = null
  supabase.auth.getUser().then(({ data: { user } }) => {
    if (!user) return  // skip realtime for anon — RLS blocks subscription anyway
    channel = supabase.channel(...).subscribe()
  })
  return () => { if (channel) supabase.removeChannel(channel) }
}, [])
```

See `references/public-private-app-pattern.md` for full app skeleton.

## ⚠️ Layout Pattern: Never Call Supabase in Layout

Calling `getServerProfile()` inside a layout causes 500 because `setSession()` is async and was not awaited before `getUser()`. Even if awaited, `cookies()` can be stale in layout context.

**Correct pattern — layout only checks cookie existence:**
```ts
// layout.tsx
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({ children }) {
  const token = cookies().get('sb-access-token')?.value
  if (!token) redirect('/login')
  return (
    <div>
      <Sidebar />  {/* Sidebar fetches its own profile client-side */}
      <main>{children}</main>
    </div>
  )
}
```

**Sidebar fetches profile client-side via useEffect:**
```ts
'use client'
useEffect(() => {
  const supabase = getSupabaseClient()
  supabase.auth.getUser().then(({ data: { user } }) => {
    if (!user) return
    supabase.from('profiles').select('*').eq('id', user.id).single()
      .then(({ data }) => { if (data) setProfile(data) })
  })
}, [])
```

## ⚠️ Event Handlers in Server Components → 500

Any component with `onMouseEnter`, `onMouseLeave`, `onClick`, etc. rendered from a Server Component causes:
```
Error: Event handlers cannot be passed to Client Component props.
```
Fix: add `'use client'` to any component that uses event handlers or React state.

## Owner-Only Mutations with Side-Effect Rollback

When a record was created by a specific user and has side effects on related rows (e.g. `pemakaian` decremented `bahan_kimia.stok_saat_ini`), deletion must:
1. Verify the caller is the original creator (ownership check)
2. Roll back the side effect (restore stock)
3. Then delete the record

**Defense-in-depth: enforce ownership BOTH in UI and in backend.** UI hides the button so the user doesn't see options they can't use; backend rejects the request so a malicious user calling the API directly can't bypass the UI.

**Backend — DELETE handler with ownership check + rollback:**
```ts
// /api/pakai/route.ts
export async function DELETE(req: NextRequest) {
  const { user, supabase } = await getCallerUser(req)
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { id } = await req.json()
  if (!id) return NextResponse.json({ error: 'id wajib diisi' }, { status: 400 })

  // Fetch the record first
  const { data: record, error } = await supabase
    .from('pemakaian')
    .select('id, user_id, bahan_id, jumlah')
    .eq('id', id)
    .single()
  if (error || !record) return NextResponse.json({ error: 'Tidak ditemukan' }, { status: 404 })

  // Ownership check — only the creator can delete
  if (record.user_id !== user.id) {
    return NextResponse.json(
      { error: 'Hanya pengguna yang membuat catatan ini yang bisa menghapusnya' },
      { status: 403 }
    )
  }

  // Roll back side effect: restore stock
  const { data: bahan } = await supabase
    .from('bahan_kimia').select('stok_saat_ini').eq('id', record.bahan_id).single()
  if (bahan) {
    await supabase.from('bahan_kimia')
      .update({ stok_saat_ini: Number(bahan.stok_saat_ini) + Number(record.jumlah) })
      .eq('id', record.bahan_id)
  }

  // Delete the record
  const { error: deleteError } = await supabase.from('pemakaian').delete().eq('id', id)
  if (deleteError) return NextResponse.json({ error: deleteError.message }, { status: 500 })
  return NextResponse.json({ success: true })
}
```

**UI — pass `currentUserId` from server component to client table:**
```ts
// app/riwayat/page.tsx (Server Component)
const profile = await getServerProfile()
return <RiwayatTable data={pemakaian} currentUserId={profile?.id || null} />

// components/RiwayatTable.tsx (Client)
{rows.map((p) => {
  const canDelete = !!currentUserId && p.user_id === currentUserId
  return (
    <tr>
      {/* ...other cells... */}
      <td>{canDelete ? <DeleteButton id={p.id} /> : <span>—</span>}</td>
    </tr>
  )
})}
```

Why pass from server, not check client-side: the server already has the verified user identity from the cookie. Client-side `supabase.auth.getUser()` may return null if localStorage was cleared mid-session (see "Client-Side Session Lost" above), causing all delete buttons to disappear even for the actual owner.

**Verification checklist — run all five before declaring an ownership feature done.** UI-hiding alone is not protection; backend must reject too. Side-effect rollback must be verified by inspecting the source row, not by trusting the response.

1. **Owner UI shows action button** — log in as creator, navigate to record. Delete/edit button visible.
2. **Owner can perform action** — perform delete/edit. Record disappears or updates. Side effect (stock, balance, etc.) rolls back to pre-mutation value. Verify by reading the affected row directly, not by reloading the table.
3. **Non-owner UI hides action button** — log in as different authenticated user. Action column shows "—" or no button for records owned by others.
4. **Non-owner API attempt → 403** — in browser console as the non-owner, fetch the API directly. Bypassing UI must still fail:
   ```js
   fetch('/api/pakai', {
     method: 'DELETE',
     headers: { 'Content-Type': 'application/json' },
     credentials: 'include',
     body: JSON.stringify({ id: '<other-users-record-id>' })
   }).then(r => r.json().then(d => ({ status: r.status, ...d })))
   // → { status: 403, error: 'Hanya pengguna yang membuat catatan ini...' }
   ```
5. **Anonymous API attempt → 401** — clear cookies, retry the same fetch. Must reject before any DB read:
   ```js
   document.cookie = 'sb-access-token=; path=/; max-age=0'
   // ... fetch as above → { status: 401, error: 'Unauthorized' }
   ```

If any of (3), (4), (5) fail, the feature is not safe to ship — regardless of how nice the UI looks.

This same pattern applies to any mutation that needs ownership: edit own posts, cancel own bookings, withdraw own submissions. The structure is always: fetch → verify ownership → reverse side effects → mutate.

## ⚠️ Foreign Key Cascade: Deleting Parent Silently Deletes Children

When a child table has `bahan_id UUID REFERENCES bahan_kimia(id) ON DELETE CASCADE`, deleting a parent row destroys ALL child rows that referenced it — silently, no error, no warning. Common in Supabase starter schemas because cascade is the default for clean fixture cleanup.

**Verify before shipping any "delete parent" feature** — this often surprises users who expect history/audit trails to persist:
```python
# Probe FK behavior with a throwaway pair
import urllib.request, json
# 1. Create parent
# 2. Create child referencing parent
# 3. DELETE parent
# 4. Query child by id → if [] returned, FK is ON DELETE CASCADE
```

Three options when users want delete to NOT obliterate history:

**Option A — Soft delete (recommended for audit-sensitive apps)**
Add `is_archived BOOLEAN DEFAULT false` (and optionally `archived_at TIMESTAMPTZ`). Filter queries by `.eq('is_archived', false)`. "Delete" UI flips the flag. Restore is trivial. Riwayat stays intact because the row still exists.
```sql
ALTER TABLE bahan_kimia ADD COLUMN IF NOT EXISTS is_archived boolean DEFAULT false;
ALTER TABLE bahan_kimia ADD COLUMN IF NOT EXISTS archived_at timestamptz;
```
```ts
// All public reads
.from('bahan_kimia').select('*').eq('is_archived', false)

// "Delete" handler
.from('bahan_kimia').update({ is_archived: true, archived_at: new Date().toISOString() }).eq('id', id)
```

**Option B — Block delete when children exist (RESTRICT FK)**
Change FK to `ON DELETE RESTRICT`. Postgres refuses the delete if any child references it. UI must surface the error politely.
```sql
ALTER TABLE pemakaian DROP CONSTRAINT pemakaian_bahan_id_fkey;
ALTER TABLE pemakaian ADD CONSTRAINT pemakaian_bahan_id_fkey
  FOREIGN KEY (bahan_id) REFERENCES bahan_kimia(id) ON DELETE RESTRICT;
```
API handler returns user-friendly error:
```ts
const { error } = await supabase.from('bahan_kimia').delete().eq('id', id)
if (error?.code === '23503') {
  return NextResponse.json({
    error: 'Bahan tidak bisa dihapus karena masih ada riwayat pemakaian. Hapus riwayatnya dulu atau arsipkan bahan ini.'
  }, { status: 409 })
}
```

**Option C — Cascade but snapshot child fields**
Keep cascade. Before deleting parent, copy denormalized fields (nama, satuan, kategori) into child rows so child reports remain readable even after parent is gone.
```sql
ALTER TABLE pemakaian ADD COLUMN bahan_nama_snapshot text;
ALTER TABLE pemakaian ADD COLUMN bahan_satuan_snapshot text;
```
```ts
// Before delete, snapshot
await supabase.rpc('snapshot_pemakaian_for_bahan', { _bahan_id: id })
// snapshot_pemakaian_for_bahan: UPDATE pemakaian SET bahan_nama_snapshot = b.nama, bahan_satuan_snapshot = b.satuan FROM bahan_kimia b WHERE pemakaian.bahan_id = _bahan_id AND b.id = _bahan_id
await supabase.from('bahan_kimia').delete().eq('id', id)
```

**Decision rule:**
- Audit/compliance/legal need full history → A
- User confirms "are you sure" UX is sufficient + reversibility matters → A
- Strict referential integrity, want to force users to clean up first → B
- Operational data where parent deletion is rare and reports are denormalized anyway → C

When showing the cascade warning in a confirm modal, be explicit: "Bahan akan dihapus permanen beserta semua riwayat pemakaiannya" — users frequently don't expect cascade.

## CRUD Resource API Route Pattern

For resource management (bahan kimia, products, etc.) with service role:

```ts
// src/app/api/bahan/route.ts
import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

const SUPABASE_URL = 'https://yourref.supabase.co'

function getAdminClient() {
  return createClient(SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

export async function GET() {
  const { data, error } = await getAdminClient().from('bahan_kimia').select('*').order('nama')
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ bahan: data })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const { nama, kategori, satuan, stok_saat_ini, stok_minimum } = body
  if (!nama || !kategori || !satuan)
    return NextResponse.json({ error: 'nama, kategori, satuan wajib diisi' }, { status: 400 })

  const { data, error } = await getAdminClient()
    .from('bahan_kimia').insert({ nama, kategori, satuan,
      stok_saat_ini: Number(stok_saat_ini) || 0,
      stok_minimum: Number(stok_minimum) || 0,
    }).select().single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ bahan: data })
}

export async function PUT(req: NextRequest) {
  const { id, ...fields } = await req.json()
  if (!id) return NextResponse.json({ error: 'id wajib diisi' }, { status: 400 })

  const { data, error } = await getAdminClient()
    .from('bahan_kimia').update(fields).eq('id', id).select().single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ bahan: data })
}

export async function DELETE(req: NextRequest) {
  const { id } = await req.json()
  if (!id) return NextResponse.json({ error: 'id wajib diisi' }, { status: 400 })

  const { error } = await getAdminClient().from('bahan_kimia').delete().eq('id', id)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ success: true })
}
```

## Adding Optional Columns to Existing Tables

When adding a new optional field (e.g. `deskripsi`) to an existing table:

```sql
-- Safe to run multiple times
ALTER TABLE bahan_kimia ADD COLUMN IF NOT EXISTS deskripsi text;
```

Also update the TypeScript type:
```ts
export interface BahanKimia {
  // ... existing fields
  deskripsi?: string | null;  // optional
}
```

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Database error creating new user` | Trigger missing/broken OR `email` column missing in profiles | Re-create trigger; add `email` column if missing |
| Login loads forever, no redirect | Supabase stores session in localStorage, middleware can't read it | Write tokens to cookies manually in `signIn()`, then use `window.location.href` not `router.push` |
| Login stuck at "Masuk..." spinner | `signIn()` returns no session — Supabase client initialized with `undefined` URL/key | Add hardcoded fallback for `NEXT_PUBLIC_*` vars in supabase.ts |
| `npm error Exit handler never called!` | npm cache corrupted (disk full) or npm version bug on Vercel | `npm cache clean --force` then use `--prebuilt` deploy |
| `Module has no exported member 'getUser'` | Wrong import from auth-server | Use `getServerProfile()` or cookie-based auth in API routes |
| `Cannot redeclare block-scoped variable` | Duplicate `const adminClient` | Remove duplicate declaration |
| `@supabase/ssr` type errors | Incompatible with @types/react v18 | Remove `@supabase/ssr`, use `@supabase/supabase-js` directly |
| `yarn install` network error on Vercel | yarnpkg.com timeout in Vercel DC | Remove `yarn.lock` + `packageManager` field, use npm with `--prebuilt` |
| 500 on all pages after Supabase upgrade | `@supabase/supabase-js` > 2.39.8 crashes on Node 20 (WebSocket) | Downgrade: `npm install @supabase/supabase-js@2.39.8` |
| 500 on dashboard after login | Layout calls `getServerProfile()` which fails silently | Layout only checks cookie; Sidebar fetches profile client-side |
| `supabaseKey is required` at build | `createClient` called at module level with server-only env var | Wrap in factory function, call inside handler |
| `Error: Event handlers cannot be passed to Client Component props` | Component with onClick/onMouseEnter rendered from Server Component | Add `'use client'` to the component |
| New route returns 404 on Vercel but exists locally | Used `next build` instead of `vercel build --prod` — `.vercel/output/functions/` not populated | Always use `vercel build --prod --token <TOKEN>` for prebuilt deploys |
| `column not found in schema cache` on INSERT/UPDATE | Column added to DB but Supabase schema cache not refreshed, or column doesn't exist yet | Wait ~30s for cache refresh, or remove field from payload until migration confirmed |
| Vercel `?decrypt=true` returns `decrypted: false` | Sensitive env vars cannot be decrypted via Vercel API | Run SQL in Supabase dashboard directly, or use a temporary API route |
| TopNav/Sidebar shows "Masuk" mid-session despite valid cookie | localStorage cleared but cookie persisted; client `getUser()` returns null | Restore session from cookie via `setSession()` at mount — see "Client-Side Session Lost" |
| Client-side `supabase.from(...).insert()` silently fails after navigation | Same as above — auth session lost in client | Mutate via server API route that reads cookie + uses service role |
| Public homepage `[]` from anon key | RLS blocks anon SELECT by default | Use service role on server-side fetch, or add public read policy |
| Vercel build fails: `'err' is defined but never used` | Next.js default ESLint config errors on unused vars in `catch (err)` | Use `try { ... } catch { ... }` (no binding) or `catch (_err)` if older TS, or rename to `_err` |
| `duplicate key value violates unique constraint "profiles_pkey"` on createUser | Auth trigger already inserted profile row before API tried explicit insert | Use `upsert({...}, { onConflict: 'id' })` instead of `insert()` |
| `Property 'email' does not exist on type 'Profile'` | Profile type predates `email` column | Add `email?: string` to Profile type |
| Change password succeeds but next API call returns 401 | Supabase invalidates session after password change | Re-sign-in with new password and rotate `sb-access-token`/`sb-refresh-token` cookies in the change-password response |
| `animate-in slide-in-from-top-2` classes do nothing | `tailwindcss-animate` plugin not installed | Either install plugin (`npm i -D tailwindcss-animate` + add to `plugins:` in config) or remove the classes |
