# Login Rate Limit (Lockout) — Full Implementation

Complete reference: 5 failed attempts → 15 min lockout, with countdown UI, admin reset, and end-to-end tests. No DDL required — uses `auth.users.app_metadata` JSON.

## File Layout

```
src/app/api/auth/login/route.ts          # Custom login with rate limit
src/app/api/admin/reset-lockout/route.ts # Admin-only unlock
src/app/api/admin/users/route.ts         # User list with locked/failed_attempts (modified)
src/app/admin/page.tsx                   # Locked badge + Reset Lockout button (modified)
src/app/login/page.tsx                   # Countdown timer + disable inputs when locked (modified)
```

## Constants

```ts
const MAX_ATTEMPTS = 5          // tune to 3 for stricter, 10 for more lenient
const LOCKOUT_MINUTES = 15      // tune to 5 / 30 / 60
```

Empirical observation: 15 minutes is the sweet spot — long enough to deter brute force, short enough that users don't ragequit. 5 attempts means a single typo doesn't immediately punish; 3 is too strict for users with messy passwords.

## /api/auth/login/route.ts

```ts
import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://yourref.supabase.co'
const MAX_ATTEMPTS = 5
const LOCKOUT_MINUTES = 15

function getAdminClient() {
  return createClient(SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

interface AppMeta {
  failed_attempts?: number
  locked_until?: string | null
  [key: string]: unknown
}

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()
    if (!email || !password) {
      return NextResponse.json({ error: 'Email dan password wajib diisi' }, { status: 400 })
    }

    const admin = getAdminClient()

    // Find the user. listUsers() is fine for <1k users; for larger systems,
    // maintain email→id in `profiles` and SELECT from there to avoid full scans.
    const { data: usersList, error: listErr } = await admin.auth.admin.listUsers()
    if (listErr) {
      return NextResponse.json({ error: 'Gagal memuat user' }, { status: 500 })
    }
    const user = usersList.users.find((u) => u.email === email)

    // 1. Lockout check — runs even if user not found, returns same generic error
    //    to avoid email enumeration. (Optionally add a fixed delay for non-existent
    //    emails to fully equalize timing.)
    if (user) {
      const meta = (user.app_metadata || {}) as AppMeta
      if (meta.locked_until && new Date(meta.locked_until) > new Date()) {
        const secondsLeft = Math.ceil(
          (new Date(meta.locked_until).getTime() - Date.now()) / 1000
        )
        return NextResponse.json(
          {
            error: 'Akun terkunci sementara karena terlalu banyak percobaan login',
            locked: true,
            secondsLeft,
          },
          { status: 429 }
        )
      }
    }

    // 2. Verify password — use anon client (admin client bypasses password)
    const anon = createClient(SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
    const { data: signInData, error: signInError } = await anon.auth.signInWithPassword({
      email,
      password,
    })

    // 3. Failure path — increment counter, lock if threshold reached
    if (signInError || !signInData?.session) {
      if (user) {
        const meta = (user.app_metadata || {}) as AppMeta
        const next = (meta.failed_attempts || 0) + 1
        const newMeta: AppMeta = { ...meta, failed_attempts: next }

        if (next >= MAX_ATTEMPTS) {
          newMeta.locked_until = new Date(Date.now() + LOCKOUT_MINUTES * 60_000).toISOString()
        }

        await admin.auth.admin.updateUserById(user.id, { app_metadata: newMeta })

        const remainingAttempts = Math.max(0, MAX_ATTEMPTS - next)
        const justLocked = next >= MAX_ATTEMPTS

        return NextResponse.json(
          {
            error: 'Email atau password salah',
            remainingAttempts,
            ...(justLocked ? { locked: true, secondsLeft: LOCKOUT_MINUTES * 60 } : {}),
          },
          { status: justLocked ? 429 : 401 }
        )
      }
      // Email not found — return same generic error, no counter
      return NextResponse.json({ error: 'Email atau password salah' }, { status: 401 })
    }

    // 4. Success — reset counter, set cookies
    if (user) {
      const meta = (user.app_metadata || {}) as AppMeta
      if (meta.failed_attempts || meta.locked_until) {
        await admin.auth.admin.updateUserById(user.id, {
          app_metadata: { ...meta, failed_attempts: 0, locked_until: null },
        })
      }
    }

    const response = NextResponse.json({ success: true })
    const maxAge = signInData.session.expires_in || 3600
    response.cookies.set('sb-access-token', signInData.session.access_token, {
      path: '/', maxAge, sameSite: 'lax',
    })
    response.cookies.set('sb-refresh-token', signInData.session.refresh_token, {
      path: '/', maxAge: 60 * 60 * 24 * 30, sameSite: 'lax',
    })
    return response
  } catch (err) {
    console.error('Login error:', err)
    return NextResponse.json({ error: 'Terjadi kesalahan' }, { status: 500 })
  }
}
```

## /api/admin/reset-lockout/route.ts

```ts
import { createClient } from '@supabase/supabase-js'
import { NextRequest, NextResponse } from 'next/server'

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://yourref.supabase.co'

function getAdminClient() {
  return createClient(SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

async function getCallerProfile(req: NextRequest) {
  const token = req.cookies.get('sb-access-token')?.value
  if (!token) return null
  const admin = getAdminClient()
  const { data: { user } } = await admin.auth.getUser(token)
  if (!user) return null
  const { data } = await admin
    .from('profiles')
    .select('id, role')
    .eq('id', user.id)
    .single()
  return data
}

export async function POST(req: NextRequest) {
  const profile = await getCallerProfile(req)
  if (!profile) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (profile.role !== 'guru') {
    return NextResponse.json({ error: 'Hanya guru yang bisa reset lockout' }, { status: 403 })
  }

  const { userId } = await req.json()
  if (!userId) return NextResponse.json({ error: 'userId wajib diisi' }, { status: 400 })

  const admin = getAdminClient()
  const { data: { user } } = await admin.auth.admin.getUserById(userId)
  if (!user) return NextResponse.json({ error: 'User tidak ditemukan' }, { status: 404 })

  await admin.auth.admin.updateUserById(userId, {
    app_metadata: { ...user.app_metadata, failed_attempts: 0, locked_until: null },
  })
  return NextResponse.json({ success: true })
}
```

## /api/admin/users/route.ts — Add locked/failed_attempts to response

```ts
// Inside GET handler, after fetching profiles + auth users
const enriched = profiles.map((p: any) => {
  const authUser = authUsersById.get(p.id)
  const meta = (authUser?.app_metadata || {}) as { failed_attempts?: number; locked_until?: string | null }
  const isLocked = meta.locked_until && new Date(meta.locked_until) > new Date()
  return {
    ...p,
    locked: !!isLocked,
    failed_attempts: meta.failed_attempts || 0,
    locked_until: isLocked ? meta.locked_until : null,
  }
})
return NextResponse.json({ users: enriched })
```

## Login Page (excerpt) — Countdown + Disable on Lock

```tsx
'use client'
import { useState, useEffect } from 'react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [warning, setWarning] = useState<string | null>(null)
  const [locked, setLocked] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  // Countdown tick
  useEffect(() => {
    if (!locked || secondsLeft <= 0) return
    const t = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          setLocked(false)
          setError(null)
          return 0
        }
        return s - 1
      })
    }, 1000)
    return () => clearInterval(t)
  }, [locked, secondsLeft])

  function formatTime(s: number) {
    const m = Math.floor(s / 60)
    const ss = s % 60
    return `${m}:${ss.toString().padStart(2, '0')}`
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (locked) return
    setLoading(true)
    setError(null)
    setWarning(null)

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()

    if (res.ok) {
      window.location.href = '/'
      return
    }

    if (data.locked) {
      setLocked(true)
      setSecondsLeft(data.secondsLeft || 900)
      setError(data.error)
    } else {
      setError(data.error)
      if (typeof data.remainingAttempts === 'number' && data.remainingAttempts <= 2) {
        setWarning(`Sisa percobaan: ${data.remainingAttempts}`)
      }
    }
    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit}>
      {locked && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
          <p className="font-medium text-red-900">Akun Terkunci Sementara</p>
          <p className="text-sm text-red-700 mt-1">
            Coba lagi dalam <span className="font-mono font-semibold">{formatTime(secondsLeft)}</span>
          </p>
        </div>
      )}
      {!locked && warning && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 mb-3 text-sm text-amber-800">
          {warning}
        </div>
      )}
      {error && !locked && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 mb-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={locked || loading}
        // ...
      />
      <div className="relative">
        <input
          type={showPassword ? 'text' : 'password'}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={locked || loading}
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          disabled={locked || loading}
        >
          {/* eye icon */}
        </button>
      </div>

      <button type="submit" disabled={locked || loading}>
        {locked ? `Tunggu ${formatTime(secondsLeft)}` : loading ? 'Masuk...' : 'Masuk'}
      </button>
    </form>
  )
}
```

## Admin Page — Locked Badge + Reset Button

```tsx
{users.map((u) => (
  <tr key={u.id}>
    <td>{u.nama}</td>
    <td>{u.email}</td>
    <td>{u.role}</td>
    <td>
      {u.locked ? (
        <span className="px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-800">
          Terkunci ({u.failed_attempts}/5)
        </span>
      ) : u.failed_attempts > 0 ? (
        <span className="text-xs text-amber-700">Gagal: {u.failed_attempts}/5</span>
      ) : (
        <span className="text-xs text-slate-500">—</span>
      )}
    </td>
    <td>
      {u.locked && (
        <button
          onClick={() => handleResetLockout(u.id)}
          className="px-2 py-1 text-xs rounded bg-amber-50 hover:bg-amber-100 text-amber-700"
        >
          Reset Lockout
        </button>
      )}
    </td>
  </tr>
))}
```

```ts
async function handleResetLockout(userId: string) {
  if (!confirm('Reset lockout untuk user ini?')) return
  const res = await fetch('/api/admin/reset-lockout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ userId }),
  })
  if (res.ok) {
    fetchUsers()  // refresh list
  } else {
    const data = await res.json()
    alert(data.error || 'Gagal reset lockout')
  }
}
```

## End-to-End curl Test

Verify the full happy + sad path before declaring done:

```bash
BASE=https://your-app.vercel.app

# 1. Wrong password 5x — expect remainingAttempts to count down 4,3,2,1,0
for i in 1 2 3 4 5; do
  echo "Attempt $i:"
  curl -s -X POST "$BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"wrong\"}" | python3 -m json.tool
done

# 2. After 5 fails, even CORRECT password should reject with 429
curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"correctpassword\"}" | python3 -m json.tool
# Expect: { "error": "Akun terkunci...", "locked": true, "secondsLeft": ~900 }

# 3. Admin reset (login as guru first to get cookie)
GURU_COOKIE=$(curl -s -i -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"guru@example.com","password":"gurupass"}' \
  | grep -i 'set-cookie: sb-access-token' | sed 's/.*sb-access-token=\([^;]*\).*/\1/')

curl -s -X POST "$BASE/api/admin/reset-lockout" \
  -H "Content-Type: application/json" \
  -H "Cookie: sb-access-token=$GURU_COOKIE" \
  -d "{\"userId\":\"<user-uuid>\"}" | python3 -m json.tool
# Expect: { "success": true }

# 4. After reset, correct password should succeed
curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"correctpassword\"}" | python3 -m json.tool
# Expect: { "success": true }
```

## Verification Checklist

Before declaring rate-limit feature done, all five must pass:

1. **5x wrong password → counter increments 4,3,2,1,0 in response** — confirms increment is working.
2. **6th attempt with WRONG password returns 429 + secondsLeft ~900** — confirms lockout triggered.
3. **6th attempt with CORRECT password ALSO returns 429** — confirms lockout is checked BEFORE password verification, no bypass.
4. **Admin reset endpoint clears the lockout** — login works again immediately after reset.
5. **Auto-unlock after 15 min** — wait or set a short TTL temporarily, then verify login works without admin intervention.

If (3) fails (correct password succeeds during lockout), the check is in the wrong order — must run lockout check before `signInWithPassword`.

## Why Not Use a Dedicated Table

A dedicated `login_attempts` table is cleaner conceptually but requires DDL. In environments where service role key is encrypted and SQL Editor isn't accessible from automation (Vercel sensitive env vars cannot be decrypted via API), `app_metadata` is the only path that works without manual dashboard intervention. If you DO have SQL access, a table with `(user_id, attempted_at, success)` rows gives you better audit history and lets you implement IP-based limits too.

## Email Enumeration Caveat

The current implementation responds with `remainingAttempts` only when the user exists. An attacker could probe whether an email is registered by watching the response shape. Mitigations:
- Return identical response (no `remainingAttempts`) for both "user not found" and "wrong password" paths.
- Add a fixed delay (~200ms) for non-existent emails to equalize timing.
- For high-security apps, log all failed attempts to a separate table and rate-limit by IP, not just by user.

For school/internal apps where users are pre-created by an admin, enumeration risk is low and the better UX of "Sisa percobaan: 2" outweighs the small information leak.
