# Hermes Ecosystem Tools Installation Guide

This reference documents installation patterns for Hermes ecosystem tools (GUIs, orchestration frameworks, monitoring dashboards) discovered from ecosystem catalogs.

## Ecosystem Catalog Repos

These are **directories/lists**, not installable tools:

| Repo | Purpose | Action |
|------|---------|--------|
| `0xNyk/awesome-hermes-agent` | Curated list of skills, tools, integrations | Clone → extract tool repos |
| `ksimback/hermes-ecosystem` | Map of all ecosystem projects | Clone → read ECOSYSTEM.md |
| `cclank/Hermes-Wiki` | Architecture documentation | Reference only |

## Installable Tools

### 1. Hermes Control Interface (Web Dashboard)

**Repo:** `xaspx/hermes-control-interface`  
**Type:** Node.js web app  
**Purpose:** Web-based dashboard for managing Hermes Agent

**Installation:**
```bash
cd ~ && git clone https://github.com/xaspx/hermes-control-interface.git
cd hermes-control-interface
npm install
cp .env.example .env
```

**Configuration:**
```bash
# Generate secrets
openssl rand -hex 32  # For HERMES_CONTROL_PASSWORD
openssl rand -hex 32  # For HERMES_CONTROL_SECRET

# Edit .env
nano .env
# Set HERMES_CONTROL_PASSWORD and HERMES_CONTROL_SECRET
```

**Run:**
```bash
npm run dev
# Access at http://localhost:10272
```

**Pitfall:** Node.js v18 shows engine warnings but works. Ignore `EBADENGINE` warnings for `rolldown` and `vite`.

---

### 2. Hermes HUD (Terminal Monitoring)

**Repo:** `joeynyc/hermes-hud`  
**Type:** Python TUI (Textual)  
**Purpose:** Terminal dashboard for monitoring agent activity

**Installation:**
```bash
cd ~ && git clone https://github.com/joeynyc/hermes-hud.git
cd hermes-hud
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[neofetch]"
```

**Run:**
```bash
~/hermes-hud/venv/bin/hermes-hud
# Or with venv activated:
hermes-hud
```

**CLI Modes:**
```bash
hermes-hud --text          # Print summary to stdout
hermes-hud --snapshot      # Save snapshot
hermes-hud --ai            # AI awakening neofetch
hermes-hud --br            # Blade Runner neofetch
hermes-hud --fsociety      # fsociety neofetch
```

**Pitfall:** Not available on PyPI. Must install from source. Requires Python 3.11+.

**Pitfall:** `pip install -e .` fails with "missing build_editable hook" error. Use `make dev` or manual venv + `pip install -e ".[neofetch]"`.

---

### 3. Maestro (Multi-Agent Orchestration)

**Repo:** `ReinaMacCredy/maestro`  
**Type:** Bun/TypeScript CLI  
**Purpose:** Local-first conductor for multi-agent software engineering

**Prerequisites:**
```bash
# Install Bun if not present
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
```

**Installation:**
```bash
cd ~ && git clone https://github.com/ReinaMacCredy/maestro.git
cd maestro
bun install
bun run build
```

**Run:**
```bash
export PATH="$HOME/.bun/bin:$PATH"
cd ~/maestro
./dist/maestro --help
```

**Add to PATH (optional):**
```bash
echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/maestro/dist:$PATH"' >> ~/.bashrc
source ~/.bashrc
maestro --help
```

**Pitfall:** Bun must be in PATH. After installing Bun, either `source ~/.bashrc` or manually export PATH in current shell.

---

### 4. Hermes Skill Factory (Meta-Skill Plugin)

**Repo:** `Romanescu11/hermes-skill-factory`  
**Type:** Hermes skill + plugin  
**Purpose:** Auto-generate reusable skills from workflows

**Installation:**
```bash
cd ~/.hermes/skills
git clone https://github.com/Romanescu11/hermes-skill-factory.git
cd hermes-skill-factory
bash install.sh
```

**Activation:**
```bash
hermes skills reload
hermes skills enable skill-factory
```

**Usage:**
```bash
# In Hermes session:
/skill-factory propose   # View detected skills
/skill-factory generate  # Generate skill from pattern
```

**Pitfall:** Installs to `~/.hermes/skills/meta/skill-factory/` and `~/.hermes/plugins/skill_factory.py`. Must reload skills after installation.

---

## Common Patterns

### Node.js Tools
- Clone → `npm install` → configure `.env` → `npm run dev`
- Check for `.env.example` and copy to `.env`
- Generate secrets with `openssl rand -hex 32`

### Python Tools
- Clone → create venv → `pip install -e .` or `pip install -e ".[extras]"`
- Check for `make dev` target in Makefile
- Watch for "externally-managed-environment" errors → use venv

### Bun/TypeScript Tools
- Install Bun first if missing
- Clone → `bun install` → `bun run build`
- Add Bun to PATH: `export PATH="$HOME/.bun/bin:$PATH"`

### Hermes Plugins/Skills
- Clone to `~/.hermes/skills/` or `~/.hermes/plugins/`
- Run install script if present
- Reload skills: `hermes skills reload`
- Enable: `hermes skills enable <name>`

---

## Troubleshooting

### "command not found" after installing Bun
```bash
# Reload shell config
source ~/.bashrc
# Or manually export
export PATH="$HOME/.bun/bin:$PATH"
```

### "externally-managed-environment" pip error
```bash
# Use venv instead of system Python
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### npm EBADENGINE warnings
- Usually safe to ignore if installation completes
- Tools built for Node 20+ may warn on Node 18 but still work

### Skill Factory not showing in skills list
```bash
hermes skills reload
hermes skills list | grep skill-factory
# If still missing, check installation path:
ls -la ~/.hermes/skills/meta/skill-factory/
```
