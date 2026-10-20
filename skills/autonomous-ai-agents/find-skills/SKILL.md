---
name: find-skills
description: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
---

# Find Skills

This skill helps you discover and install skills from the open agent skills ecosystem.

## When to Use This Skill

Use this skill when the user:

- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Expresses interest in extending agent capabilities
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain (design, testing, deployment, etc.)
- Shares a GitHub repo link and asks whether to install its skills ("cek semua", "should I install these", "bagus gak")

## What is the Skills CLI?

The Skills CLI (`npx skills`) is the package manager for the open agent skills ecosystem. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools.

**Key commands:**

- `npx skills find [query]` - Search for skills interactively or by keyword
- `npx skills add <package>` - Install a skill from GitHub or other sources
- `npx skills check` - Check for skill updates
- `npx skills update` - Update all installed skills

**Browse skills at:** https://skills.sh/

## How to Help Users Find Skills

### Step 1: Understand What They Need

When a user asks for help with something, identify:

1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is a common enough task that a skill likely exists

### Step 2: Check Ecosystem Catalogs FIRST

**CRITICAL:** Before creating custom skills or searching skills.sh, check if the user has shared ecosystem catalog repos (Awesome lists, Atlas/Ecosystem directories). These contain curated tools, GUIs, and integrations that may solve the need WITHOUT requiring skill installation.

**When user shares a full repo link asking "should I install?":** This is an overlap evaluation, not a search. Load `references/skill-overlap-evaluation.md` for the comparison workflow — inventory repo skills, compare against `skills_list`, check format compatibility, assess domain relevance, then present a structured recommendation.

Common Hermes ecosystem catalogs:
- `awesome-hermes-agent` — Curated list of tools, skills, plugins
- `hermes-ecosystem` / `hermes-atlas` — Map of all ecosystem projects
- `hermes-wiki` — Architecture documentation

**Workflow:**
1. If user shares GitHub repos → clone and explore FIRST
2. Distinguish between:
   - **Catalogs/directories** (just lists of links) → extract relevant tool repos
   - **Actual tools** (Control Interface, HUD, Maestro) → install directly
   - **Skill libraries** (wondelai/skills, Anthropic-Cybersecurity-Skills) → install skills
3. Only create custom skills if the specific need is NOT covered by ecosystem

### Step 3: Check the Leaderboard

After checking ecosystem catalogs, check the [skills.sh leaderboard](https://skills.sh/) to see if a well-known skill already exists for the domain. The leaderboard ranks skills by total installs, surfacing the most popular and battle-tested options.

For example, top skills for web development include:
- `vercel-labs/agent-skills` — React, Next.js, web design (100K+ installs each)
- `anthropics/skills` — Frontend design, document processing (100K+ installs)

### Step 4: Search for Skills

If the leaderboard doesn't cover the user's need, run the find command:

```bash
npx skills find [query]
```

For example:
- User asks "how do I make my React app faster?" → `npx skills find react performance`
- User asks "can you help me with PR reviews?" → `npx skills find pr review`
- User asks "I need to create a changelog" → `npx skills find changelog`

**Note on `npx skills` vs `hermes skills`:**
- `npx skills` — Standalone Skills CLI (Node.js-based package manager)
- `hermes skills` — Hermes Agent's built-in skill manager (Python-based)
Both access the same skill registry. Use `hermes skills` when working inside Hermes sessions; use `npx skills` for standalone management.

### Step 3b: Add External Repositories as Taps (Vercel Labs Example)

For ecosystems outside the main hub (e.g., Vercel Labs, `awesome-claude-skills`), add the repo as a tap to enable searching:

```bash
# Add Vercel Labs skills repository as a source
npx skills tap add https://github.com/vercel-labs/skills
hermes skills tap add https://github.com/vercel-labs/skills   # within Hermes

# Now search across that source
npx skills find [query]
hermes skills search [query]   # within Hermes
```

This populates results from that repository's index. The tap is persistent — it remains configured until explicitly removed.

### Step 4: Verify Quality Before Recommending

**Do not recommend a skill based solely on search results.** Always verify:

1. **Install count** — Prefer skills with 1K+ installs. Be cautious with anything under 100.
2. **Source reputation** — Official sources (`vercel-labs`, `anthropics`, `microsoft`) are more trustworthy than unknown authors.
3. **GitHub stars** — Check the source repository. A skill from a repo with <100 stars should be treated with skepticism.

### Step 5: Present Options to the User

When you find relevant skills, present them to the user with:

1. The skill name and what it does
2. The install count and source
3. The install command they can run
4. A link to learn more at skills.sh

Example response:

```
I found a skill that might help! The "react-best-practices" skill provides
React and Next.js performance optimization guidelines from Vercel Engineering.
(185K installs)

To install it:
npx skills add vercel-labs/agent-skills@react-best-practices

Learn more: https://skills.sh/vercel-labs/agent-skills/react-best-practices
```

### Step 6: Offer to Install

If the user wants to proceed, you can install the skill for them directly within Hermes:

```bash
# With auto-confirmation (non-interactive)
printf "y\n" | hermes skills install <ID> -y

# Or interactively: hermes skills install <ID>  (then confirm prompts)
```

The `-y` flag skips confirmation prompts (use cautiously). The ID can be:
- A hub identifier (e.g., `vercel-labs/agent-skills@react-best-practices`)

**Example (from Vercel Labs):**
```bash
```

### Step 6b: Handle Installation Pitfalls

When installing from external GitHub repos, several common issues arise:

**Pitfall 1 — Category selection prompt defaults to a single letter (e.g., `y`)**

After the security scan, Hermes prompts:
```
Pick a category (reuse an existing bucket, type a new one, or press Enter to install flat)
Category:
```

If you send a bare `y` (or press Enter), the skill lands under `~/.hermes/skills/y/`. Fix:
```bash
# Move to a proper category AFTER install
mv ~/.hermes/skills/y/find-skills ~/.hermes/skills/autonomous-ai-agents/
```

Better: provide the category name at the prompt:
```
Category: autonomous-ai-agents
```

**Pitfall 2 — Security scan blocks skill installation with "Verdict: CAUTION / BLOCKED"**

Skills containing build configs, path-like references (e.g., `[skills-reference/...]`), or Scaffold-ETH patterns may trigger false positives:
```
Decision: BLOCKED — Blocked (community source + caution verdict, 3 findings).
Use --force to override.
```

Resolution:
- If source is reputable (vercel-labs, austintgriffith, high-star GitHub repo), override with `--force`:
  ```bash
  hermes skills install <URL> --name <skill> --force
  ```
- **Note:** When `--force` is already on the command, the "BLOCKED" message is **informational only** — the install proceeds anyway. The skill will be installed successfully despite the BLOCKED output. Verify with `hermes skills list | grep <skill>`.



The file path inside the repo is **not standardized**. Common patterns:

```bash
curl -fsSL "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" | grep -i "<skill-name>"
```
Then construct the raw URL from the discovered path.

**Pitfall 3b — `npx skills add` hangs in non-interactive contexts**

`npx skills add <owner/repo@skill>` prompts interactively for agent selection ("Which agents do you want to install to?") and will hang if stdin is not a TTY. **Always prefer `hermes skills install <raw-URL> --name <name> --force`** for automated/agent-driven installs. Use `npx skills find` for search only.

**Pitfall 4 — Skill shows as `disabled` after moving**

After relocating a skill to the correct category, verify enablement:
```bash
hermes skills list | grep <skill>
hermes skills config   # See category enablement matrix
```
If disabled, enable the category for your current platform or run `/reset` to reload all skills.

**Pitfall 5 — GitHub API rate limit blocks tree discovery AND hermes skills install**

When installing multiple skills in one session, the GitHub API rate limit (60 req/hr unauthenticated) exhausts quickly. Symptoms:
- `hermes skills install` fails with "GitHub API rate limit exhausted"
- Tree API returns `{"message":"API rate limit exceeded..."}`
- Even `hermes skills install <raw-URL>` fails because it internally calls the API

Workarounds (in priority order):
2. **Git clone the repo** when you need many files or can't find the path:
   ```bash
   cd /tmp && git clone --depth 1 https://github.com/<owner>/<repo>.git
   ```
3. **Common path patterns** (try these before burning API calls):
4. Set `GITHUB_TOKEN` in `.env` for 5,000 req/hr limit
5. For reference/script files, `curl -sf` from raw.githubusercontent.com works without the API

**Manual skill installation when rate-limited:**
```bash
# 1. Clone repo
cd /tmp && git clone --depth 1 https://github.com/<owner>/<repo>.git
# 2. Create skill directory
SKILL_DIR="$HOME/.hermes/skills/<category>/<skill-name>"
mkdir -p "$SKILL_DIR/references" "$SKILL_DIR/scripts"
# 3. Copy files
cp /tmp/<repo>/path/to/references/*.md "$SKILL_DIR/references/"
# 4. Fix frontmatter name if needed (must match directory name)
# 5. Verify: hermes skills list | grep <skill-name>
```

**Pitfall 6 — `npx skills add` hangs on interactive agent selection**


1. Check the GitHub repo tree: `curl -fsSL "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" | grep <skill-name>`
3. Install: `printf "category\n" | hermes skills install "<raw-URL>" --name <skill> --force`

---

## Common Skill Categories

When searching, consider these common categories:

| Category        | Example Queries                          |
| --------------- | ---------------------------------------- |
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing         | testing, jest, playwright, e2e           |
| DevOps          | deploy, docker, kubernetes, ci-cd        |
| Documentation   | docs, readme, changelog, api-docs        |
| Code Quality    | review, lint, refactor, best-practices   |
| Design          | ui, ux, design-system, accessibility     |
| Productivity    | workflow, automation, git                |
| Trading/Finance | trading, forex, crypto, technical analysis, macro, news, economic calendar |
| Trading/Finance | trading forex crypto, technical analysis, risk management |

### Trading & Finance Skills (Verified Working)

The skills.sh ecosystem has trading skills. Search `trading forex crypto` to find them. Top verified picks (as of 2025):

| Skill | Source | Coverage |
|-------|--------|----------|


**Pitfall 6 — Plugin-style skills (with dist/, src/, package.json) need full directory copy**

```bash
cd /tmp && git clone --depth 1 https://github.com/<owner>/<repo>.git
SKILL_DIR="$HOME/.hermes/skills/<category>/<skill-name>"
mkdir -p "$SKILL_DIR"
cp -r /tmp/<repo>/path/to/skill/* "$SKILL_DIR/"
npm install --prefix "$SKILL_DIR"
# Verify dist/ exists; if not: npm run build --prefix "$SKILL_DIR"
hermes skills list | grep <skill-name>
```
NEVER cd into the skill directory for npm commands; use `--prefix` instead.


```bash
# Discover file paths in the repo
curl -fsSL "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" | grep "<skill-name>"
# Download each file to the skill directory
SKILL_DIR="$HOME/.hermes/skills/<category>/<skill-name>"
mkdir -p "$SKILL_DIR/references" "$SKILL_DIR/scripts"
curl -fsSL "https://raw.githubusercontent.com/<owner>/<repo>/main/<path>/<file>" -o "$SKILL_DIR/references/<file>"
```
| Trading/Finance | trading, forex, crypto, technical analysis, risk management |

## Tips for Effective Searches

1. **Use specific keywords**: "react testing" is better than just "testing"
2. **Try alternative terms**: If "deploy" doesn't work, try "deployment" or "ci-cd"
3. **Check popular sources**: Many skills come from `vercel-labs/agent-skills` or `ComposioHQ/awesome-claude-skills`
4. **Browser search on skills.sh is more reliable for niche domains**: `hermes skills search` may return nothing for specialized topics (e.g., trading, forex, crypto) while the skills.sh website search returns many results. When CLI search fails, navigate to `https://skills.sh/` and use the search box directly.
5. **Niche domains have lower install counts**: Trading/finance skills typically have 20-600 installs (vs 100K+ for web dev). Adjust quality thresholds accordingly — 200+ installs is solid for niche domains.

## When No Skills Are Found

If no relevant skills exist:

1. **FIRST**: Check ecosystem repos (Awesome Hermes Agent, Hermes Atlas, community skill libraries) for existing solutions
2. **SECOND**: Search skills.sh and GitHub for related skills in other repos
3. **THIRD**: If truly nothing exists, acknowledge and offer alternatives:
   - Help with the task directly using general capabilities
   - Suggest creating a custom skill with `npx skills init`

**CRITICAL**: Do NOT immediately create custom skills when the user asks for something. Always search the ecosystem first. Many common needs (database management, API development, testing, data analysis) already have community solutions.

**Real failure cases from sessions:**

**Case 1: Premature custom skill creation**
- User shared 10 Hermes ecosystem repos (Awesome Hermes Agent, Hermes Atlas, Skill Factory, etc.)
- Agent immediately created 7 custom skills (docker-compose, fastapi-development, postgres-management, pandas-analysis, matplotlib-plotting, security-testing, load-testing)
- User corrected: "Kenapa anda buat sendiri? Ini kan sudah ada biar anda lebih pintar install ini tuh" (Why did you make it yourself? These already exist so you can be smarter by installing them)
- **Correct approach**: Clone repos → explore → distinguish catalogs from actual skills → install existing skills → only create custom if gaps remain

**Case 2: Not searching before building**
- User asked for pump.fun monitoring dashboard with screening
- Agent started building from scratch
- User corrected: "Coba anda find skills lagi agar website bisa tambah fitur lebih bagus... find skills meme coin atau pumpfun"
- **Correct approach**: Search skills.sh for "pump.fun", "meme coin", "crypto trading" FIRST → found 5+ relevant skills (pumpfun, meme-scout, whale-tracking, liquidity-analysis, custom-indicators) → install them → THEN build using their knowledge
- **Key lesson**: ALWAYS search ecosystem before building, even for seemingly custom/niche domains

**When custom skills ARE appropriate:**
- User's need is highly domain-specific (e.g., Indonesian academic formatting, company-specific workflow)
- Existing skills use wrong framework/approach for user's context
- User explicitly requests custom creation after seeing existing options
- You've confirmed the gap exists after thorough ecosystem search

Example workflow:

```
Let me search the ecosystem for existing skills first...
[Check Awesome Hermes Agent catalog]
[Search skills.sh]
[Check community repos like wondelai/skills, Anthropic-Cybersecurity-Skills]

Found: [list existing options]
OR
No existing skills found. I can:
1. Help you directly with this task
2. Create a custom skill if you need it repeatedly
```

---

## Post-Installation Checklist

After installing any skill:

- [ ] `hermes skills list` confirms the skill is `enabled` in the correct category
- [ ] If category is wrong (e.g., `y`), move the skill directory to the intended category
- [ ] Reload skills in current session: `/reset` (in chat) or restart Hermes CLI
- [ ] Test the skill: ask a question that would trigger it or load explicitly with `/skill <name>`
- [ ] If the skill provides tools, verify they appear: `hermes tools list` or ask the agent to use them

Document the skill's purpose and trigger phrases in your personal notes so future sessions remember why you installed it.

### Step 7: When GitHub API Rate Limit Is Exhausted

If `hermes skills install` fails with "GitHub API rate limit exhausted", clone the repo directly:

```bash
cd /tmp && git clone --depth 1 https://github.com/<owner>/<repo>.git
```

Then manually copy files:
```bash
SKILL_DIR="$HOME/.hermes/skills/<category>/<skill-name>"
mkdir -p "$SKILL_DIR/references"
cp /tmp/<repo>/skills/<name>/references/*.md "$SKILL_DIR/references/"
```


## Reference Files

- `references/skill-overlap-evaluation.md` — Evaluate a shared skill repo against existing skills: overlap detection, format compatibility, domain relevance, decision matrix. Use when user shares a repo link and asks "should I install these?"
- `references/batch-install-workflow.md` — Optimized workflow for installing multiple skills at once (parallel search, URL resolution via tree API, sequential install with category piping). Includes a real-world example from a thesis project.
- `references/trading-forex-crypto-skills.md` — Curated landscape of trading/forex/crypto skills on skills.sh with install commands, quality notes, and recommendations.
- `references/pump-fun-meme-coin-skills.md` — Pump.fun & meme coin skills ecosystem: pumpfun API (32 tools), meme-scout, whale-tracking, liquidity-analysis, custom-indicators. Includes WebSocket integration patterns, screening criteria, and common red/green flags.
- `references/web3-bot-automation-skills.md` — Curated toolkit for building web3 automation bots (Node.js): browser automation (Puppeteer/Playwright), EVM wallet (ethers.js), Solana wallet (Helius/Phantom), NFT minting (Manifold), social auth (X/Discord). Includes resolved paths, install commands, architecture diagram, and gaps requiring custom code.
- `references/hermes-ecosystem-tools.md` — Installation patterns for Hermes ecosystem tools (Control Interface, HUD, Maestro, Skill Factory). Covers Node.js, Python, Bun/TypeScript tools with pitfalls and troubleshooting.
