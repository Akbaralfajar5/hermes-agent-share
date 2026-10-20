# Verify Subagent Output Before Claiming Success

## The Failure Mode

Subagent runs `delegate_task`, gets `"status": "completed"` or
`"status": "timeout"` in the result, and the controller proceeds as if the
work is done. **The subagent's status field tells you nothing about whether
the artifact actually exists.**

Real session example:

```
delegate_task(goal="Create PowerPoint at /path/to/PPT_Seminar.pptx", ...)
→ result: {"status": "completed", "tool_trace": [...]}
controller: replies "Done — PPT created"

# Reality, when user complains:
$ ls /path/to/PPT_Seminar.pptx
ls: No such file or directory
```

In another case the subagent timed out at 600s with 8 API calls completed
but the file path was empty (`0 bytes`). The trace showed only one
`terminal` call, no `write_file`. The work never started.

## Always Verify After Delegation

After ANY `delegate_task` whose deliverable is a file or set of files:

```python
import os

# 1. File exists?
target = '/path/to/output.pptx'
exists = os.path.exists(target)

# 2. Non-empty?
size = os.path.getsize(target) if exists else 0

if not exists or size < 100:
    # Don't claim success. Either retry directly (in controller) or re-dispatch.
    print(f"Subagent claimed completion but file missing/empty: exists={exists} size={size}")
    # → fix in controller using execute_code or write_file directly
```

For multi-file deliverables, verify ALL of them in one shell:

```bash
ls -la /path/to/file1 /path/to/file2 /path/to/file3
# Or with size guards:
for f in file1 file2 file3; do
    [ -s "/path/$f" ] || echo "MISSING/EMPTY: $f"
done
```

## When Subagent Times Out

If `result.status == "timeout"`:

1. **Do not assume partial progress is usable.** Check the file that was
   supposed to exist; usually it doesn't, or is 0 bytes (the subagent died
   mid-write).
2. **Do not redispatch the same goal blindly.** A 600s timeout usually means
   the goal was too large for one subagent OR the subagent got stuck in a
   slow API call. Either:
   - Break the task into 2-3 smaller subagents, OR
   - Do it directly in the controller using `execute_code` / `write_file`.
3. **Switch to controller-direct execution for single-file artifacts.**
   Most "create one HTML file" or "create one .docx" tasks are faster done
   directly than via delegation, especially if the content is mostly known.

## Trace Inspection

The `tool_trace` in `delegate_task` results gives you ground truth on what
actually happened:

```python
result = delegate_task(...)
# Look at status of last few calls:
trace = result.get('tool_trace', [])
for t in trace[-3:]:
    print(t['tool'], t.get('status'), t.get('result_bytes', 0))
```

A trace that ends with a `terminal` call returning 121 bytes and no
subsequent `write_file` means the subagent never persisted output, no
matter what the summary claims.

## Pattern: Belt-and-Suspenders Delegation

For high-value artifacts (final docx, deck the user is waiting on):

```
1. Dispatch subagent with clear file_path goal.
2. Verify file exists and size > MIN_BYTES.
3. If verification fails:
   a. Inspect trace for last error.
   b. Switch to controller-direct execution.
4. Only then announce success to user.
```

The user never wants a "completed" status. They want the file. Verify the
file before you say "done".

## Related

  review for file-output tasks.
