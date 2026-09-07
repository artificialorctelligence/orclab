---
name: secret-hygiene
description: Use before running or pasting anything that could surface a credential - debugging auth, reading config/env/log files, dumping environment variables, inspecting keyrings or token stores, or sharing command output. Keeps secrets out of the transcript, and gives the recovery procedure when one is exposed anyway.
---

# Secret Hygiene

The failure mode this skill exists to close off isn't mishandling a secret you knew you were
handling — it's printing one you weren't thinking about, in the middle of unrelated work, because
the command that emitted it looked like a diagnostic rather than a disclosure.

That distinction matters because it decides *when* this skill has to fire. It is not "use when
working with secrets." Nobody sets out to leak one. It is "use when touching the surfaces where
secrets live," which is a much wider and much more boring set of moments: debugging why an auth
token isn't working, `cat`-ing a config file, dumping the environment to compare two processes,
reading a CI log, checking why a deploy 401s.

## Why a printed secret is different from a written one

A secret written to a file can be edited out. A secret *printed by a tool* cannot be recalled. In
one step it lands in all of:

- the model's context, and every subsequent API request, since the whole conversation is re-sent
  each turn
- the session transcript on disk (`~/.claude/projects/<slug>/<session-id>.jsonl`), permanently
- the rendered scrollback on the user's screen
- any transcript search, export, or session-resume that later reads that file

There is no undo. The only remediation is rotation, which is the user's work, not yours.

## The rules

**Never run a command whose purpose is to emit a secret.** Where a masked equivalent exists, it is
not a preference, it is the only acceptable form:

| Don't | Do |
|---|---|
| `gh auth token` | `gh auth status` (self-masks) |
| `cat ~/.aws/credentials`, `cat .env` | `grep -c` for presence, or redact on read (below) |
| `env`, `printenv` | `env \| sed -E 's/=.*//'` — keys only |
| `echo $API_KEY` to "confirm it's set" | `[ -n "$API_KEY" ] && echo set` |

**When a secret must be read, never let it cross stdout.** Redirect it into a file or a variable,
use it there, and clean up in the same command:

```bash
TOK=$(get-the-secret 2>/dev/null)
curl -s -o /dev/null -w 'http=%{http_code}\n' -H "Authorization: token $TOK" https://api.example.com/v1/me
```

**Verify by effect, not by value.** An HTTP status, an exit code, a byte count, or a checksum
proves a credential works. The credential itself proves nothing extra and costs everything.

**Redact when reading files that may hold secrets:**

```bash
sed -E 's/((token|secret|password|passwd|api[_-]?key|authorization)[[:space:]]*[:=][[:space:]]*).*/\1<redacted>/I' path/to/config
```

**Never put a secret anywhere it gets copied onward:** not in a URL or query string, not in a
commit message, not in a `BACKLOG.md` entry, an issue, a PR body, a published artifact, or a
memory file. `environment-registry` already states the matching rule for live environments —
register the environment, never its credentials.

**Assume unfamiliar output may contain one.** Before pasting a log, a stack trace, or a config
dump into the conversation, scan it. Ask whether this specific output needed to be shown in full,
or whether the two relevant lines would have done.

## Enforcement, and its limits

Orclab ships a `PreToolUse` hook (`hooks/scripts/secret_guard.py`) that denies the narrow set of
Bash commands whose entire stdout *is* a credential — `gh auth token`, a bare `env`, `cat` of a
credential file, `echo $*_TOKEN`, secret-manager reads. Every denial names the safe alternative,
so being blocked should redirect the work rather than stop it.

Treat it as a backstop, not a substitute for the rules above. It only knows the patterns someone
thought of in advance, it deliberately permits the captured forms (`TOK=$(...)`, `... > file`),
and it fails open on any internal error — a guard that wedges every Bash call would be a worse
outcome than the leak it prevents. The judgment is still yours; the hook only catches the
reflexive cases.

If a denial is genuinely wrong, re-run with a trailing `# orclab:allow-secret`. That escape hatch
is intentionally explicit rather than silent: it puts the decision in the transcript where the
user can see it was made.

## When one leaks anyway

Do not minimize it and do not bury it in a later paragraph. In this order:

1. **Say it immediately and plainly**, at the top of the next response, before continuing the task.
   The user cannot decide how urgent it is if they don't know it happened.
2. **Give the rotation command first**, before any explanation. Rotation is time-sensitive;
   the post-mortem is not.
3. **Then trace the real scope, and check rather than assume** — which exact command emitted it,
   how many copies exist on disk (`grep -rlE '<pattern>' ~/.claude/projects/ …`), and critically,
   *where it did not go*. "It was sent to the API it authenticates, over TLS, which already had it"
   is a materially different exposure than "it was pushed to a public repo," and the user needs the
   accurate version to size their response.
4. **Offer cleanup, flagging what makes it awkward** — scrubbing a transcript that the running
   session is still appending to, for instance. Say so rather than issuing a command that may
   conflict.

## The incident that produced this skill

2026-09-07, diagnosing a "GitHub CLI authentication expired" banner. Testing whether `gh` could
still reach its token with the keyring unreachable, a session ran:

```bash
env -i HOME=$HOME PATH=/usr/bin:/bin gh auth token --hostname github.com 2>&1
```

and printed a live `gho_` token into the transcript. Every *other* command in that same
investigation had handled the token correctly — `gh auth status` self-masked, and an earlier API
check redirected to a temp file and echoed only a four-character prefix. The leak came from the
one call whose entire output *was* the secret, run reflexively as a diagnostic.

Two lessons, and the second is the one worth keeping:

- `gh auth token` is a disclosure command, not a diagnostic. So are its equivalents everywhere else.
- **Careful handling on four out of five commands is not careful handling.** Secret hygiene has no
  partial credit — it is decided by the single worst line, and that line is usually the one typed
  without thinking because the task at hand was something else entirely.
