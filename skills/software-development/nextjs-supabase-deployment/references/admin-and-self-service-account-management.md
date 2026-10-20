# Admin Panel + Self-Service Profile (Multi-Role)

End-to-end pattern for an in-app account management system where:
- Any user with role `guru` can create accounts (siswa OR another guru) — cascading admin rights
- Default password mode (`123456`) for batch onboarding, custom mode for security-sensitive
- Every user (guru + siswa) can change their own password via `/profil`
- Wrong-current-password rejects (400), non-guru hitting create endpoint rejects (403)


## File Layout

```
src/app/admin/page.tsx                       # Admin UI (guru-only)
src/app/profil/page.tsx                      # Self-service profile + change password (any user)
src/app/api/admin/create-user/route.ts       # POST — guru creates siswa or guru
src/app/api/admin/delete-user/route.ts       # DELETE — guru deletes (existing)
src/app/api/admin/users/route.ts             # GET — list all (existing)
src/app/api/profile/change-password/route.ts # POST — verifies current pw, updates, rotates cookies
src/components/TopNav.tsx                    # Adds /profil link to siswa+guru nav
src/middleware.ts                            # Adds /profil to PROTECTED_ROUTES
src/types/index.ts                           # Adds email?: string to Profile
```

## API: create-user with Role Selector + Default Password

```ts
// src/app/api/admin/create-user/route.ts
import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

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
    .from('profiles').select('id, role').eq('id', user.id).single()
  return profile
}

const DEFAULT_PASSWORD = '123456'

export async function POST(request: NextRequest) {
  const profile = await getCallerProfile(request)
  if (!profile) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (profile.role !== 'guru')
    return NextResponse.json({ error: 'Hanya guru yang bisa membuat akun' }, { status: 403 })

  const adminClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )

  const { nama, email, password, kelas, role } = await request.json()
  if (!nama || !email)
    return NextResponse.json({ error: 'Nama dan email wajib diisi' }, { status: 400 })

  const newUserRole = role === 'guru' ? 'guru' : 'siswa'
  if (newUserRole === 'siswa' && !kelas)
    return NextResponse.json({ error: 'Kelas wajib diisi untuk siswa' }, { status: 400 })

  const finalPassword = password && password.length >= 6 ? password : DEFAULT_PASSWORD
  const usedDefault = !password || password.length < 6

  const { data: newUser, error: createError } = await adminClient.auth.admin.createUser({
    email, password: finalPassword, email_confirm: true,
    user_metadata: { nama, kelas: kelas || null }
  })
  if (createError) return NextResponse.json({ error: createError.message }, { status: 400 })

  // ⚠️ UPSERT not INSERT — auth trigger may have created the row already
  const { error: profileError } = await adminClient
    .from('profiles')
    .upsert({
      id: newUser.user.id,
      nama, email,
      kelas: newUserRole === 'siswa' ? kelas : null,
      role: newUserRole,
    }, { onConflict: 'id' })

  if (profileError) {
    await adminClient.auth.admin.deleteUser(newUser.user.id)
    return NextResponse.json({ error: profileError.message }, { status: 500 })
  }

  return NextResponse.json({
    success: true,
    user: { id: newUser.user.id, nama, email,
            kelas: newUserRole === 'siswa' ? kelas : null, role: newUserRole },
    password: finalPassword,
    usedDefault,
  })
}
```

## API: change-password with Re-Auth + Cookie Rotation

```ts
// src/app/api/profile/change-password/route.ts
import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const accessToken = request.cookies.get('sb-access-token')?.value
  if (!accessToken) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const adminClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )

  const { data: { user }, error: tokenErr } = await adminClient.auth.getUser(accessToken)
  if (tokenErr || !user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { currentPassword, newPassword } = await request.json()
  if (!newPassword || newPassword.length < 6)
    return NextResponse.json({ error: 'Password baru minimal 6 karakter' }, { status: 400 })
  if (!currentPassword)
    return NextResponse.json({ error: 'Password saat ini wajib diisi' }, { status: 400 })

  // Re-auth check: prove caller knows current password
  const anonClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )
  const { error: signInErr } = await anonClient.auth.signInWithPassword({
    email: user.email!, password: currentPassword,
  })
  if (signInErr) return NextResponse.json({ error: 'Password saat ini salah' }, { status: 400 })

  // Update password
  const { error: updateErr } = await adminClient.auth.admin.updateUserById(user.id, {
    password: newPassword,
  })
  if (updateErr) return NextResponse.json({ error: updateErr.message }, { status: 500 })

  // ⚠️ Refresh tokens — Supabase invalidates session on password change
  const { data: refreshData } = await anonClient.auth.signInWithPassword({
    email: user.email!, password: newPassword,
  })

  const response = NextResponse.json({
    success: true,
    session: refreshData?.session ? {
      access_token: refreshData.session.access_token,
      refresh_token: refreshData.session.refresh_token,
      expires_in: refreshData.session.expires_in,
    } : null,
  })

  if (refreshData?.session) {
    const maxAge = refreshData.session.expires_in || 3600
    response.cookies.set('sb-access-token', refreshData.session.access_token,
      { path: '/', maxAge, sameSite: 'lax' })
    response.cookies.set('sb-refresh-token', refreshData.session.refresh_token,
      { path: '/', maxAge: 60 * 60 * 24 * 30, sameSite: 'lax' })
  }
  return response
}
```

## Admin UI Highlights

Key UX patterns from `src/app/admin/page.tsx`:

- **Role selector** as a 2-button group (not dropdown). Visual diff between selected vs unselected via bg color (teal for siswa, amber for guru).
- **Password mode toggle** also as 2-button group. Default mode hides the password input entirely; custom mode shows it with eye toggle.
- **Created credentials card** shown after success — monospace font, `nama:`/`email:`/`password:` rows, copy button using `navigator.clipboard.writeText()`. Tooltip flips to "Tersalin" for 2 seconds.
- **Filter tabs** above user list (Semua / Guru / Siswa) using a pill segmented control inside `bg-slate-100 p-1 rounded-lg`.
- **Stat counter in header** (`{users.length} akun · {guruCount} guru · {siswaCount} siswa`).
- **Self-protection** — `isSelf = user.id === callerId` hides the delete button for the caller's own row, replacing it with an "Anda" badge.
- **Guru deletion warning** in confirm modal: amber banner reminding "Pastikan masih ada minimal 1 guru aktif setelah penghapusan."

## Profile Page UI

`src/app/profil/page.tsx` is two cards stacked:

1. **Info akun** — avatar (gradient circle, color depends on role), nama + role badge + email, kelas if siswa.
2. **Ubah password** form with three `PasswordField` components (current / new / confirm), each with eye toggle. Shared `PasswordField` component avoids duplication.

Validation order in `handleSubmit`:
1. `newPassword !== confirmPassword` → "Konfirmasi password tidak cocok"
2. `newPassword.length < 6` → "Password baru minimal 6 karakter"
3. `currentPassword === newPassword` → "Tidak boleh sama dengan password saat ini"
4. POST to `/api/profile/change-password` — server returns more granular errors

After success, clear all 3 fields and show success banner. Do NOT logout — cookies are already rotated by the API.

## Test Script (Python)


Specific cases for this flow:
1. Guru utama creates new guru with default password → 200, password=`123456`, usedDefault=true
2. New guru logs in with `123456` → 200
3. New guru creates a siswa (custom password, with kelas) → 200
4. New guru changes own password → 200
5. Re-login with new password → 200
6. Siswa logs in, changes own password → 200
7. Siswa POSTs to `/api/admin/create-user` → 403 "Hanya guru yang bisa membuat akun"
8. Wrong currentPassword on change → 400 "Password saat ini salah"
9. Cleanup: delete test users via admin client

## Common Bugs Caught

- **`duplicate key value violates unique constraint "profiles_pkey"`** — used `insert()` instead of `upsert()`. Auth trigger fired first.
- **TS error: `Property 'email' does not exist on type 'Profile'`** — added email to type definition (optional).
- **Build fail: unused import `Mail`/`Lock`** — when removing icons from a form, remove from import list too. ESLint blocks build.
- **Build fail: unused param `refreshToken`** — Next ESLint forbids unused vars; remove or prefix with `_`.

## Middleware Update

```ts
const PROTECTED_ROUTES = [
  '/kelola-bahan',
  '/admin',
  '/pakai',
  '/riwayat',
  '/profil',  // ← add new gated route here
]
```

## TopNav Links

```ts
const siswaLinks = [
  { href: '/pakai', label: 'Pakai Bahan', icon: ListPlus },
  { href: '/riwayat', label: 'Riwayat', icon: History },
  { href: '/profil', label: 'Profil Saya', icon: UserCircle },
]

const guruLinks = [
  { href: '/pakai', label: 'Pakai Bahan', icon: ListPlus },
  { href: '/riwayat', label: 'Riwayat', icon: History },
  { href: '/kelola-bahan', label: 'Kelola Bahan', icon: Beaker },
  { href: '/admin', label: 'Manajemen Akun', icon: Settings2 },
  { href: '/profil', label: 'Profil Saya', icon: UserCircle },
]
```
