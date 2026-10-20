# Hermes Control Interface — Customization

Workflow for customizing branding, login flow, and display names in Hermes Control Interface.

## Password-Only Login (Remove Username)

By default, HCI uses username + password authentication. To simplify to password-only:

### 1. Frontend HTML (`src/index.html`)

**Login form — remove username input:**
```html
<!-- Before -->
<div class="login-sub" id="login-sub">Enter credentials to continue</div>
<form id="login-form" class="login-form">
  <input id="login-username" type="text" placeholder="Username" autocomplete="username" />
  <input id="login-password" type="password" placeholder="Password" autocomplete="current-password" />
  <button type="submit" class="btn btn-primary">unlock</button>
</form>

<!-- After -->
<div class="login-sub" id="login-sub">Enter password to continue</div>
<form id="login-form" class="login-form">
  <input id="login-password" type="password" placeholder="Password" autocomplete="current-password" />
  <button type="submit" class="btn btn-primary">unlock</button>
</form>
```

**Setup form (first run) — remove username input:**
```html
<!-- Before -->
<form id="setup-form" class="login-form" style="display:none;">
  <div class="login-sub">First run — create admin account</div>
  <input id="setup-username" type="text" placeholder="Username" autocomplete="username" />
  <input id="setup-password" type="password" placeholder="Password (min 8 chars)" autocomplete="new-password" />
  <input id="setup-password-confirm" type="password" placeholder="Confirm password" autocomplete="new-password" />
  <button type="submit" class="btn btn-primary">create admin</button>
</form>

<!-- After -->
<form id="setup-form" class="login-form" style="display:none;">
  <div class="login-sub">First run — create admin password</div>
  <input id="setup-password" type="password" placeholder="Password (min 8 chars)" autocomplete="new-password" />
  <input id="setup-password-confirm" type="password" placeholder="Confirm password" autocomplete="new-password" />
  <button type="submit" class="btn btn-primary">create admin</button>
</form>
```

### 2. Frontend JavaScript (`src/js/main.js`)

**Login handler (~line 155):**
```javascript
// Remove: const username = document.getElementById('login-username').value;
// Change body to: JSON.stringify({ password })
```

**Setup handler (~line 186):**
```javascript
// Remove: const username = document.getElementById('setup-username').value;
// Change body to: JSON.stringify({ password })
```

### 3. Backend (`server.js`)

**Setup endpoint (`/api/auth/setup`, ~line 1865):**
```javascript
// Before:
const { username, password } = req.body || {};
if (!username || !password) { ... }

// After:
const { password } = req.body || {};
const username = 'admin'; // Fixed username
if (!password) { ... }
```

**Login endpoint (`/api/auth/login`, ~line 1891):**
```javascript
// Before:
const { username, password } = req.body || {};
if (!username || !password) { ... }
error: 'Invalid username or password'

// After:
const { password } = req.body || {};
const username = 'admin'; // Fixed username
if (!password) { ... }
error: 'Invalid password'
```

**Key insight:** Backend uses `process.env.HOST || '127.0.0.1'` for listen address. The username is hardcoded to 'admin' in the backend — authentication still works normally, just the frontend doesn't ask for it.

## Branding Customization

### Change Application Name

Three locations in `src/index.html`:

1. **Browser tab title** (line 9):
   ```html
   <title>Your Custom Name</title>
   ```

2. **Login page brand** (line 24):
   ```html
   <div class="login-brand">Your Custom Name</div>
   ```

3. **Dashboard header** (line 48):
   ```html
   <div class="brand-sub">Your Custom Name</div>
   ```

### Change User Display Name

In `src/js/main.js`, function `updateUserMenu()` (~line 143):

```javascript
function updateUserMenu() {
  if (!state.user) return;
  // Change from: state.user.username
  document.getElementById('user-name').textContent = 'your display name';
  document.getElementById('user-role').textContent = state.user.role;
  // ...
}
```

**Note:** This only changes the display. Backend username remains 'admin' for auth purposes.

### Change Logo/Favicon

Replace files:
- `src/assets/hermes-icon.svg` — header logo
- `src/assets/favicon.svg` — browser tab icon

## After Changes

**Restart required:**
- Frontend changes: Stop and restart `npm run dev` (Vite hot-reload may pick up HTML/JS changes automatically in dev mode)
- Backend changes: Stop and restart `node server.js`
- `.env` changes: Stop and restart `node server.js`

**Verify:**
```bash
curl -s http://<SERVER_IP>:5173 | grep -E "login-brand|<title>"
```

## Pitfalls

- **First-run state:** If you modify the setup form but the database already has a user, the setup form won't show. Delete the SQLite database to reset: `rm ~/hermes-control-interface/*.db`
- **Vite caching:** Hard refresh (Ctrl+Shift+R) in browser if changes don't appear
- **nvm context:** Always `source ~/.nvm/nvm.sh && nvm use 20` before running npm/node commands
- **Background processes:** Kill old Vite/Node processes before restarting: `pkill -f "vite\|node server.js"`
