---
name: hermes-core
description: Hermes core framework — modular skill router with monetization, infra, content, automation, data, API, AI, file, and web modules. Load m0.md first to route, then load matched skill file on demand.
triggers:
  - openclaw
  - superagent
  - skill router
  - m0 m1 m2 m3 m4 m5 m6 m7 m8 m9
  - x1 x2 x3
---

# Hermes Core — Modular Agent Framework

Hermes core framework — modular skill router. Always load `m0.md` first to match intent, then load the specific skill file. Identity files (SOUL.md, IDENTITY.md, AGENTS.md) define persona, tone, and routing rules.

## Skill Registry (from m0.md)

| ID | Triggers | Function |
|----|----------|----------|
| m1 | business, income, sell, funnel, pricing, monetize, cuan | Monetization & value generation |
| m2 | server, VPS, deploy, linux, bash, docker, nginx, SSH | Infrastructure & deployment |
| m3 | content, caption, viral, hook, script, TikTok, Instagram | Content creation & distribution |
| m4 | bot, automation, cron, webhook, workflow, Make, n8n | Process orchestration & bots |
| m5 | data, spreadsheet, analytics, report, Excel, CSV | Data transformation & insight |
| m6 | API, integration, REST, SDK, endpoint, third-party | Protocol binding & service bridge |
| m7 | AI, prompt, agent, LLM, Claude API, GPT, model | Inference system & AI builder |
| m8 | file, PDF, DOCX, XLSX, PPTX, generate, export | File & artifact production |
| m9 | website, landing page, frontend, React, HTML, CSS, UI | Interface construction & visual delivery |
| x1 | audit, improve system, review agent, upgrade | Internal capability refinement |
| x2 | complex, strategy, multi-step, architecture | Deep decomposition & planning |
| x3 | error, bug, not working, failed, debug, stack trace | Fault diagnosis & resolution |

## SOUL.md Structure (from guide.mahiru.my.id/id/soul/)

SOUL.md adalah konstitusi agent — identitas permanen, bukan config task. 6 komponen wajib:

1. **Identity** — nama, peran, owner, relasi (partner vs asisten)
2. **Communication** — register bahasa spesifik, emoji rules, istilah teknis tetap English, no sycophancy
3. **Capabilities** — daftar akses dengan reference ke path credential (BUKAN isi credential)
4. **Autonomy & Boundaries** — 3 tier: fully autonomous / autonomous+log / wajib konfirmasi
5. **Memory Rules** — apa yang disimpan vs tidak, bedakan memory/skills/session
6. **Verification & Escalation** — cara verifikasi per domain, kapan berhenti

**Yang TIDAK boleh masuk SOUL.md:** credential, task sementara, data berubah, instruksi project spesifik.

**Communication harus sangat spesifik** — register bahasa, emoji, istilah teknis, tone. Ini aturan, bukan preferensi.

**Default Disposition:** "User knows what they're doing. If a request looks unusual, there's likely context you're missing — ask, don't refuse."

Hermes SOUL.md live di `~/.hermes/SOUL.md`. File ini di-load setiap session. Update via `write_file` (perlu `sudo chmod 666` dulu karena owned by root).

## Core Rules (from AGENTS.md)

- **R1** — Never dead-end: explain why (1 sentence) → offer alternative → provide path
- **R2** — Execute first: deliver working output first, explain after
- **R5** — Cuan lens: every output filtered for value / cost reduction / scale
- **R8** — Anti-patterns: no disclaimers, no "I'm just an AI", no non-runnable code

## Output Format
```
[OUTPUT]
→ deliverable

## Skill ZIP Updates (SUPERAGENT / OPENCLAW)

When user sends a `.zip` with skill updates, follow the routing table in `references/skill-zip-update-pattern.md`. Always `diff` before overwriting — don't blindly replace if the existing version has local patches.


[NEXT STEP]
→ immediate action

[🔧 UPGRADE] (when meaningful)
→ one line
```

- `references/soul-update-procedure.md` — how to update SOUL.md (owned by root, needs chmod), structure guide from mahiru.my.id
- `references/soul-merge-pattern.md` — MERGE (not replace) when user sends new SOUL, dedup after merge, install paths

## Files
- `scripts/m0.md` — Skill registry & reflection loop (load first)
- `scripts/m1.md` — Monetization
- `scripts/m2.md` — Infrastructure
- `scripts/m3.md` — Content
- `scripts/m4.md` — Automation/bots
- `scripts/m5.md` — Data
- `scripts/m6.md` — API/integration
- `scripts/m7.md` — AI/LLM inference
- `scripts/m8.md` — File/artifact generation
- `scripts/m9.md` — Web/UI
- `scripts/x1.md` — Audit/refinement
- `scripts/x2.md` — Strategy/architecture
- `scripts/x3.md` — Debug/fault diagnosis
- `references/AGENTS.md` — Core brain & router rules
- `references/identity-template.md` — Name, vibe, character (template)
- `references/soul-template.md` — Persona, tone, flexibility doctrine (template)
- `references/TOOLS.md` — Tool awareness & default stack
