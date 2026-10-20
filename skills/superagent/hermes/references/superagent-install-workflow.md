# SUPERAGENT ZIP Install — Add-Only Workflow

When user sends a SUPERAGENT ZIP update, install into `~/.hermes/` with ADD-ONLY mode — never replace existing files.

## Flow

```bash
# 1. Unzip
unzip SUPERAGENT-v*.zip -d /tmp/superagent/

# 2. Diff existing vs new
# For references:
diff <(ls ~/.hermes/skills/trading/hermes-crypto-agent/references/) \
     <(ls /tmp/superagent/openclaw/skills/hermes/references/)
# For scripts:
diff <(ls ~/.hermes/skills/trading/hermes-crypto-agent/scripts/) \
     <(ls /tmp/superagent/openclaw/skills/hermes/scripts/)

# 3. ADD only NEW files (skip if already exists)
for f in <new_files>; do
    cp source/$f ~/.hermes/skills/trading/hermes-crypto-agent/references/$f
done

# 4. Copy tools to ~/.hermes/scripts/superagent/
mkdir -p ~/.hermes/scripts/superagent/
cp /tmp/superagent/openclaw/tools/*.py ~/.hermes/scripts/superagent/
cp /tmp/superagent/openclaw/skills/hermes/scripts/*.py ~/.hermes/scripts/superagent/

# 5. Install Python deps in Hermes venv
~/.hermes/hermes-agent/venv/bin/python -m pip install web3 eth-account httpx

# 6. Place SOUL.md at ~/.hermes/SOUL.md (user persona)
cp SOUL.md ~/.hermes/SOUL.md
```

- **ADD-ONLY** — never replace existing skills/refs/scripts
- Tools go to `~/.hermes/scripts/superagent/` (direct install, not just skills)
- Persona file at `~/.hermes/SOUL.md`
