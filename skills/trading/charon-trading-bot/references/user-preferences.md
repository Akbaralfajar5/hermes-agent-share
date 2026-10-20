# User Preferences (the user)

These are observed working preferences from live sessions. Apply them by default when working on Charon for this user.

## File structure: integrate, don't fragment

**Hard preference:** when extending Charon, append new logic to the file that already owns the closest concern. Do NOT create new standalone modules unless the existing files genuinely have no place for the new code.

User quote (May 2026 patch session): *"nama file diubah tidak apa2? Padahal biarkan aja untuk nama file yg penting isinya yg di integrasikan."* — meaning: keep the existing file names, what matters is the integrated content.

Concrete mapping observed during the Ponyin x Charon integration:

| New concern | Wrong (rejected) | Right (per user) |
|---|---|---|
| On-chain Solana checks (mint auth, wallet ages, gas fee) | new `src/enrichment/ponyin.js` | append to `src/enrichment/jupiter.js` (already has `@solana/web3.js` connection setup) |
| Rent refund / `closeEmptyTokenAccount` | new `src/execution/rentRefund.js` | append to `src/liveExecutor.js` (already holds the live `Keypair` + `solanaConnection`) |
| New filter rules | already correct: `src/pipeline/candidateBuilder.js` |  |
| Position partial-entry / DCA logic | already correct: `src/db/positions.js` + `src/execution/positions.js` |  |

Workflow: when patching, **read the file you're about to extend first** to see if it already has the imports, the cache layer, or the helper you'd otherwise create. If yes, extend in place. If no, then a new file is justified — but flag it in the summary so the user can override.

After consolidation, update `package.json` `check` script to include any newly-touched files in the `node --check` chain so syntax errors surface in `npm run check`.

## Communication

- Indonesian by default in chat replies. Code identifiers, log strings, and commit messages may stay English. BAB / A7 / Vol.1-Vol.2 nomenclature follows Ponyin canon and is intentionally Indonesian.
- Direct, short answers. The user pings *"gimana"* / *"udh?"* when responses lag — speed up, don't apologize.
- After multi-file changes, give a concise file-level summary: *what changed in which file*, not a re-explanation of the feature.
- Confirm interpretation when ambiguous, but for clear requests act first and report.

## Operational defaults

- **Hot-reload over restart.** Strategy + settings live in SQLite, read every 5s via `activeStrategy()` cache. Patch DB rows directly — don't restart `pm2`. Things that DO require restart: `.env` changes, API key changes, RPC URL changes, code changes. Flag those explicitly.
- **dry_run first, always.** Never push the user toward `live` mode without explicit go-ahead. SOL balance check before suggesting live.
- **Year is 2026** in this user's environment. Skripsi/cover dates, log timestamps, and any "current year" reference should be 2026 unless context says otherwise.
- **`pm2 save` after structural process changes** (new app, new tunnel, etc.) so it survives reboot.

## Verification expectations

- After patching JS files, run `npm run check` (or extend the script to include the file). User expects "syntax OK" before moving on.
- After DB schema/strategy edits, query back and show a row dump — user verifies by sight.
- For trading-bot changes, watch `pm2 logs charon` for at least 30s after the change and quote the first filter/decision line that proves the new code is active.

## Anti-patterns to avoid

- ❌ Splitting one logical change across many tiny new files "for clarity" — user reads as fragmentation.
- ❌ Suggesting a refactor or rename when the user only asked for a feature add.
- ❌ Lengthy preambles before tool calls. Get to the action.
- ❌ Asking the user 5 yes/no questions when 1-2 would do; pick sane defaults and proceed.
