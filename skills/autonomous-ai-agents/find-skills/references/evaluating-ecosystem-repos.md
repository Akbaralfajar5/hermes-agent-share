# Evaluating Ecosystem Repos

When a user shares GitHub repos from an ecosystem (Awesome lists, Hermes Atlas, etc.), follow this workflow to distinguish between catalogs, tools, and actual installable skills.

## Step 1: Clone and Identify Type

```bash
cd /tmp && git clone --depth 1 <repo-url>
ls -la <repo-name>/
cat <repo-name>/README.md | head -100
```

## Step 2: Classify the Repo

### Type A: Catalog/Directory (NOT installable)
**Indicators:**
- README is a curated list with links to other repos
- Contains `ECOSYSTEM.md`, `index.html`, or similar aggregation files
- Purpose: Discovery, not installation

**Examples:**
- `0xNyk/awesome-hermes-agent` — Curated list of resources
- `ksimback/hermes-ecosystem` — Map of tools and integrations
- `cclank/Hermes-Wiki` — Documentation and architecture guides

**Action:** Read the catalog to find links to actual skill repos, then explore those.

---

### Type B: Tool/Application (NOT a skill)
**Indicators:**
- Has `server.js`, `main.py`, or application entry points
- Contains `package.json` with dependencies and scripts
- README describes installation and running a service
- Purpose: Standalone application (web dashboard, CLI tool, monitoring system)

**Examples:**
- `xaspx/hermes-control-interface` — Web dashboard for managing Hermes
- `joeynyc/hermes-hud` — Terminal monitoring dashboard
- `ReinaMacCredy/maestro` — Multi-agent orchestration CLI

**Action:** Install as a separate application (not via `hermes skills install`). Follow the repo's installation instructions.

---

### Type C: Skill Library (INSTALLABLE)
**Indicators:**
- README mentions "agentskills.io" or "agent skills"
- Has skill metadata (name, description, tags)
- Purpose: Extend agent capabilities with procedural knowledge

**Examples:**
- `wondelai/skills` — Cross-platform skills library
- `mukul975/Anthropic-Cybersecurity-Skills` — 754 security skills
- `smartcontractkit/chainlink-agent-skills` — Blockchain interaction skills


---

### Type D: Skill Factory/Generator (META tool)
**Indicators:**
- README describes "auto-generating" or "creating" skills
- Contains templates or generation logic
- Purpose: Tool to help you create skills, not a skill itself

**Examples:**
- `Romanescu11/hermes-skill-factory` — Auto-generates skills from workflows

**Action:** Install as a tool/plugin, not as a skill. Use it to generate custom skills when needed.

---

## Step 3: Extract Value from Each Type

### From Catalogs (Type A):
1. Read the README/ECOSYSTEM.md
2. Identify links to Type C (skill libraries)
3. Note links to Type B (useful tools)
4. Ignore duplicate entries (same repo listed multiple times)

### From Tools (Type B):
1. Evaluate if the tool solves a user need
2. Check installation requirements (Node.js, Python, Docker, etc.)
3. Install separately from skills (follow repo's README)
4. Document installation path and usage

### From Skill Libraries (Type C):
2. Check skill quality (stars, installs, source reputation)
3. Install relevant skills via `hermes skills install`
4. Download supporting files (references/, scripts/) manually if needed

### From Skill Factories (Type D):
1. Install the factory tool
2. Use it to generate custom skills when ecosystem gaps exist
3. Don't use it as a first resort — search ecosystem first

---

## Step 4: Prioritize Actions

**Priority 1:** Install skills from Type C repos that match user needs

**Priority 2:** Install Type B tools that provide significant value (dashboards, monitoring, orchestration)

**Priority 3:** Use Type D factories only if no existing skills cover the need

**Priority 4:** Bookmark Type A catalogs for future reference

---

## Common Mistakes to Avoid

❌ **Creating custom skills before exploring ecosystem repos**
- User shares repos → Agent immediately creates custom skills
- Correct: Explore repos → find existing skills → install → create custom only if gaps remain

❌ **Treating catalogs as installable skills**
- Awesome lists are discovery tools, not skill packages
- Correct: Use catalogs to find actual skill repos

❌ **Installing tools via `hermes skills install`**
- Tools like Control Interface are applications, not skills
- Correct: Follow the tool's installation instructions (npm install, pip install, etc.)

❌ **Assuming all repos in a catalog are high quality**
- Catalogs list everything, including experimental/abandoned projects
- Correct: Verify stars, installs, and maintenance status before recommending

---

## Real Example: Hermes Ecosystem Repos

User shared 10 repos. Here's the correct classification:

| Repo | Type | Action |
|------|------|--------|
| NousResearch/hermes-agent | Core (already installed) | ✅ Skip |
| 0xNyk/awesome-hermes-agent | Catalog (Type A) | Read → find skill repos |
| ksimback/hermes-ecosystem | Catalog (Type A) | Read → find skill repos |
| cclank/Hermes-Wiki | Documentation (Type A) | Read for learning |
| xaspx/hermes-control-interface | Tool (Type B) | Install as web app |
| joeynyc/hermes-hud | Tool (Type B) | Install as CLI tool |
| ReinaMacCredy/maestro | Tool (Type B) | Install as orchestration CLI |
| nativ3ai/hermes-agent-camel | Fork (Type B) | Alternative Hermes version |
| kaminocorp/hermes-alpha | Experimental (Type B) | Research project, not production |
| Romanescu11/hermes-skill-factory | Factory (Type D) | Install for skill generation |

**From the catalogs, found actual skill libraries:**
- wondelai/skills (480 stars) → Type C → Install relevant skills
- Anthropic-Cybersecurity-Skills (4,132 stars) → Type C → Install security skills
- chainlink-agent-skills → Type C → Install blockchain skills

**Correct workflow:**
1. Clone catalogs → extract skill library links
2. Install skills from wondelai/skills, Anthropic-Cybersecurity-Skills
3. Install Control Interface + HUD as separate tools
4. Only create custom skills if gaps remain after ecosystem search

---

## Quick Decision Tree

```
User shares repo
    ↓
Clone & check README
    ↓
    ├─ YES → Type C (Skill Library) → Install skills
    └─ NO → Check for server.js/main.py
        ├─ YES → Type B (Tool) → Install as application
        └─ NO → Check for curated lists/links
            ├─ YES → Type A (Catalog) → Extract skill repo links
            └─ NO → Type D (Factory) → Install for skill generation
```
