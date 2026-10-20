# Recovering a wiped/deleted session (state.db WAL forensics)

When a session was deleted (`hermes sessions delete`, wipe cron, cleanup) and the user references it in a
fresh chat ("sesi kemarin…"), its messages are usually still recoverable for a while from SQLite free
pages / WAL frames. Session store: `~/.hermes/state.db` (tables `sessions`, `messages` + FTS mirrors).
`~/.hermes/sessions/sessions.json` is only the routing index.

## Recon before recovery
- `session_search` can return 0 while history still exists or was just wiped — confirm against
  `~/.hermes/logs/gateway.log` (`inbound message: platform=… msg='…'` lines carry user-message text)
  and `~/.hermes/scripts/delete-last-session.log`.
- Wipe pattern seen in the wild: a one-shot `no_agent` cron job ("wipe-last-session") running
  `scripts/delete-last-session.sh` → loops `hermes sessions delete <id> --yes` up to 60× with `sleep 10`
  until the row count hits 0. Deletes are REFUSED while a turn lease/compression lock is held, so the
  script retries and the session disappears right AFTER the active turn ends.
- Cron job defs live in `~/.hermes/cron/jobs.json` (large single JSON doc — text-search it).

## Recovery recipe
1. Copy `state.db`, `state.db-wal`, `state.db-shm` to scratch. NEVER checkpoint/vacuum the live DB
   (the gateway holds a writer — VACUUM-while-live is unsafe and checkpointing can evict the frames).
2. Quick probe: `strings -n 12 state.db-wal | grep -aiE "<keyword>"` — catches adjacent fragments fast.
3. Window scan (main workhorse):

```python
raw = open('state.db-wal','rb').read()
def clean(b):
    t = b.decode('utf-8','replace')
    return ''.join(ch if (ch.isprintable() or ch in '\n\t') else ' ' for ch in t)
anchors = ["<distinctive phrase 1>", "<phrase 2>"]  # include words the user just repeated in the new chat
seen = set()
for a in anchors:
    i = 0
    while True:
        i = raw.find(a.encode(), i)
        if i < 0: break
        seg = clean(raw[max(0, i-1500):i+2500])
        if seg[1000:1100] not in seen:
            seen.add(seg[1000:1100])
            print(f"===== [{a}] @{i} =====\n{seg}")
        i += 1
```

4. Write windows to a file, then read with `read_file` (pages). Keep the printable filter — `read_file`
   refuses the dump as "binary" if NUL/control bytes remain. One ≈4KB window usually reconstructs a whole
   message; windows around nearby anchors overlap, so dedupe by fingerprint.

## Pitfalls
- Sooner = better: checkpoints, VACUUM, or heavy new writes can evict the old frames.
- Keep recovered secrets/PII out of chat; use recovery to restore context, not to republish sensitive data.
- `session_search` browse returning "0 sessions" is NOT proof there was no history — check WAL + logs.

## Full local-data purge checklist (user says "hapus data lokal / sessions / chat")

1. **Sessions** — one-shot wipe job ("wipe-last-session" pattern above) deletes the session row after the current turn ends; then `hermes sessions list` shows empty.
2. **Recovery scratch** — delete any WAL copies / window dumps made for forensics (`~/.hermes/cache/scratch/rec/`, etc.).
3. **Doc cache** — `~/.hermes/cache/documents/`: remove the user's uploaded zips + extract dirs (e.g. `doc_*klaim*.zip`, `klaim_extract*`); keep tooling caches and other projects' dirs unless asked.
4. **/tmp leftovers** — sweep only files tied to this purge; ASK before deleting other projects' working files (this box keeps weeks of /tmp clutter).
5. **Log previews** — truncate `logs/gateway.log`, `logs/agent.log` + rotations (`.log.1`…): they carry `inbound message … msg='…'` previews. Leave `errors.log`.
6. **Irrecoverable purge (user runs, OUTSIDE the gateway)** — `hermes gateway stop && hermes sessions optimize && hermes gateway start`; the VACUUM clears free pages + WAL where deleted rows linger.
7. **Telegram side** — bot API cannot bulk-clear or delete user messages: tell the user to Clear history / Delete chat client-side.
8. **Unless asked otherwise** — leave memory/profile notes, skills, config, cron job defs untouched.
