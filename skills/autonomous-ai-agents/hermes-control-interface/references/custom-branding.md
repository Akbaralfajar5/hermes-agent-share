# Custom Branding Guide

Complete guide for rebranding Hermes Control Interface with custom name, logo, and styling.

## Quick Rebrand: Change Application Name

To change "Hermes Control Interface" to your custom name (e.g., "the user control interface"):

### 1. Browser Tab Title

**File:** `src/index.html` (line ~9)

```html
<!-- Before -->
<title>Hermes Control Interface</title>

<!-- After -->
<title>your custom name</title>
```

### 2. Login Page Brand

**File:** `src/index.html` (line ~24)

```html
<!-- Before -->
<div class="login-brand">Hermes Control Interface</div>

<!-- After -->
<div class="login-brand">your custom name</div>
```

### 3. Dashboard Header

**File:** `src/index.html` (line ~48)

```html
<!-- Before -->
<div class="brand-sub">Hermes Control Interface</div>

<!-- After -->
<div class="brand-sub">your custom name</div>
```

### 4. Package Metadata (Optional)

**File:** `package.json`

```json
{
  "description": "your custom name - Self-hosted web dashboard for the Hermes AI agent stack"
}
```

### 5. User Display Name (Top-Right Menu)


**File:** `src/js/main.js` (line ~145)

```javascript
// Before
function updateUserMenu() {
  if (!state.user) return;
  document.getElementById('user-name').textContent = state.user.username;
  document.getElementById('user-role').textContent = state.user.role;
  // ...
}

// After
function updateUserMenu() {
  if (!state.user) return;
  document.getElementById('user-name').textContent = 'your display name';
  document.getElementById('user-role').textContent = state.user.role;
  // ...
}
```

**Note:** This changes the **display name** only. The backend username remains "admin" for authentication.

### 6. Restart Frontend

```bash
# Kill existing Vite process
pkill -f "vite"

# Restart
cd ~/hermes-control-interface
npm run dev
```

Changes take effect immediately (Vite hot-reload for dev, or rebuild for production).

## Custom Logo

Replace default Hermes icon with your own:

### Logo Files

- `src/assets/hermes-icon.svg` - Header logo (shown in top-left)
- `src/assets/favicon.svg` - Browser tab icon

**Recommended sizes:**
- Header logo: 32x32px or scalable SVG
- Favicon: 16x16px, 32x32px, or scalable SVG

### Replace Logo

```bash
cd ~/hermes-control-interface/src/assets

# Backup originals
cp hermes-icon.svg hermes-icon.svg.bak
cp favicon.svg favicon.svg.bak

# Copy your logo
cp /path/to/your-logo.svg hermes-icon.svg
cp /path/to/your-favicon.svg favicon.svg
```

**Note:** Keep filenames as `hermes-icon.svg` and `favicon.svg` to avoid updating HTML references.

## Custom Colors

Edit theme colors in `src/css/theme.css`:

### Primary Colors

```css
:root {
  /* Brand colors */
  --primary: #2B4EA2;      /* Main accent color */
  --primary-hover: #1e3a7a;
  --secondary: #E91E7B;    /* Secondary accent */
  
  /* Background colors */
  --bg-primary: #1a1a2e;   /* Main background */
  --bg-secondary: #16213e; /* Cards, panels */
  --bg-tertiary: #0f1419;  /* Darker elements */
  
  /* Text colors */
  --text-primary: #e4e4e7;
  --text-secondary: #a1a1aa;
  --text-muted: #71717a;
}
```

### Login Page Colors

```css
.login-card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.login-brand {
  color: var(--primary);  /* Brand name color */
  font-size: 1.5rem;
  font-weight: 600;
}
```

### Button Colors

```css
.btn-primary {
  background: var(--primary);
  color: white;
  border: 1px solid var(--primary);
}

.btn-primary:hover {
  background: var(--primary-hover);
}
```

## Custom Fonts

### Add Google Fonts

**File:** `src/index.html` (in `<head>`)

```html
<!-- Replace JetBrains Mono with your font -->
<link href="https://fonts.googleapis.com/css2?family=Your+Font:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### Apply Font

**File:** `src/css/theme.css`

```css
:root {
  --font-mono: 'Your Font', monospace;
  --font-sans: 'Your Font', sans-serif;
}

body {
  font-family: var(--font-sans);
}

.login-brand, code, pre {
  font-family: var(--font-mono);
}
```

## Production Build

After customization, rebuild for production:

```bash
cd ~/hermes-control-interface
npm run build
```

Static files output to `dist/` directory.

## Complete Rebrand Checklist

- [ ] Change application name (3 places in `index.html`)
- [ ] Change user display name (1 place in `main.js`)
- [ ] Update package.json description
- [ ] Replace logo files (`hermes-icon.svg`, `favicon.svg`)
- [ ] Customize colors in `theme.css`
- [ ] Change fonts (optional)
- [ ] Update README.md with new name (optional)
- [ ] Rebuild for production (`npm run build`)
- [ ] Test login page appearance
- [ ] Test dashboard header
- [ ] Test user menu display name (top-right)
- [ ] Verify browser tab title and favicon

## Revert to Defaults

If you need to restore original branding:

```bash
cd ~/hermes-control-interface

# Restore from git
git checkout src/index.html
git checkout src/assets/hermes-icon.svg
git checkout src/assets/favicon.svg
git checkout src/css/theme.css
git checkout package.json

# Restart
npm run dev
```

## Examples

### Minimal Rebrand (Name Only)

User wants "the user control interface" instead of "Hermes Control Interface":

```bash
cd ~/hermes-control-interface/src

# Update all 3 occurrences in HTML
sed -i 's/Hermes Control Interface/the user control interface/g' index.html

# Update user display name in JavaScript

# Restart frontend
pkill -f vite
npm run dev
```

### Full Rebrand (Name + Colors)

1. Update name in `index.html` (3 places)
2. Edit `css/theme.css`:
   ```css
   :root {
     --primary: #FF6B35;      /* Orange accent */
     --secondary: #004E89;    /* Blue secondary */
     --bg-primary: #0A0E27;   /* Dark navy background */
   }
   ```
3. Replace logos in `assets/`
4. Restart: `npm run dev`

## Notes

- **Dev mode:** Changes to HTML/CSS hot-reload automatically
- **Production mode:** Must rebuild with `npm run build` after changes
- **Logo format:** SVG recommended for scalability, PNG/JPG also supported
- **Color contrast:** Ensure text remains readable after color changes
- **Font loading:** Google Fonts may slow initial load; consider self-hosting for production
