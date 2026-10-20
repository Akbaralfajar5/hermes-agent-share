# 🏭 Skill Factory

> **The meta-skill that creates skills.**
> Your AI watches your workflows and turns them into reusable Hermes skills — automatically.

Built for [Nous Research's Hermes Agent](https://github.com/NousResearch/hermes-agent) (v2026.3+).

---

## What It Does

Every time you solve a problem with Hermes, you're performing a workflow worth repeating. Skill Factory watches silently, detects patterns, and at the right moment asks:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏭 SKILL FACTORY — New Skill Detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I noticed you repeatedly set up a Python environment,
installed dependencies, and ran tests in the same order.

Proposed Skill:   python-env-setup
Category:         software-development
Description:      Reproducible Python project setup workflow

What it captures:
  1. Create venv and activate
  2. Upgrade pip and install dependencies
  3. Run pytest to verify environment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Say **C** and it writes both files immediately:

- `~/.hermes/plugins/<name>.py` — A slash command that triggers it directly

---

## Installation

**Requirements:** Hermes Agent v2026.3+

```bash
git clone https://github.com/your-username/hermes-skill-factory
cd hermes-skill-factory
bash install.sh
```

Or manually:

```bash
# Install the meta-skill
mkdir -p ~/.hermes/skills/meta/skill-factory

# Install the plugin
cp plugins/skill_factory.py ~/.hermes/plugins/
```

Then activate:

```bash
hermes skills reload
hermes skills enable skill-factory
```

---

## Usage

Once installed, Skill Factory runs in the background during every session.

| Command | What it does |
|---|---|
| `/skill-factory propose` | Analyze the session and propose the top detected skill now |
| `/skill-factory list` | List all skills generated this session |
| `/skill-factory status` | Show how many patterns are being tracked |
| `/skill-factory queue` | Show all detected patterns queued for proposal |
| `/skill-factory save <name>` | Save the last proposal with a custom name |
| `/skill-factory clear` | Clear the current session log |

**Tip:** You can also just tell Hermes naturally:
- *"Save this as a skill"*
- *"Remember how to do this"*
- *"Turn this workflow into a reusable skill"*

---

## What Gets Generated


A complete skill definition following Hermes' native skill format:

```markdown
---
name: Python Env Setup
category: software-development
description: Reproducible Python project setup
tags: [python, venv, testing]
---

# Python Env Setup

## When to Activate
...

## Workflow
### Phase 1: Environment
1. python -m venv .venv
2. source .venv/bin/activate
...

## Examples
...
```

### plugin.py

A scaffolded Hermes plugin with a slash command:

```python
def register(hermes):
    @hermes.command(name="python-env-setup", ...)
    async def run_skill(ctx, args=""):
        # Step 1: Create venv
        # Step 2: Install deps
        # Step 3: Run tests
        ...
```

---

## Repo Structure

```
hermes-skill-factory/
├── skills/
│   └── skill-factory/
├── plugins/
│   └── skill_factory.py      # Plugin: /skill-factory commands
├── templates/
│   ├── SKILL_TEMPLATE.md     # Template for generated skills
│   └── PLUGIN_TEMPLATE.py    # Template for generated plugins
├── examples/
│   └── generated/
│       └── git-pr-workflow/  # Example of a Skill Factory output
├── docs/
│   └── how-it-works.md       # Architecture deep-dive
└── install.sh                # One-command installer
```

---

## How It Works

See [docs/how-it-works.md](docs/how-it-works.md) for a full breakdown.

**TL;DR:**
2. `skill_factory.py` provides the `/skill-factory` commands and file generation
3. You work normally — Skill Factory watches silently and proposes at the right moment

---

## Examples

The `examples/generated/` directory contains real example outputs from Skill Factory:


---

## Contributing

PRs welcome. If you've generated a great skill using Skill Factory, consider adding it to `examples/generated/` with a PR.

---

## License

MIT
