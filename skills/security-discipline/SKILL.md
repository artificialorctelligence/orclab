---
name: security-discipline
description: Background rules for any code Claude is about to write or change, in any language - what every project owes (secrets out of the repo and the artifact, dependencies audited, downloads verified, least permission) and what a project strangers can reach owes on top (every network input hostile, every route authenticated, errors that leak nothing, encrypted transport, rate limits). Each rule traced to OWASP or CWE, with where each stack's tooling enforces it. Not a command; Claude reads it whenever code is about to be written, and /orc-code asks the one question that decides the tier.
user-invocable: false
---

# Security Discipline

`code-discipline` says how code is shaped. This says what it must never let in or let out. Nine
rules in two tiers, each traced to OWASP or CWE so the next reader can judge it rather than take
it on trust. The candidate list was the OWASP Top 10:2025, OWASP ASVS 5.0.0 and the 2025 CWE Top
25, read live on 2026-09-19 (confirmed live 2026-09-19); what survived is what maps to a linter
rule some stack's tooling has, a piece `/orc-code` scaffolds, or a command — everything else is a
review item at most, and the reason there are nine and not a hundred is the same as
`code-discipline`'s: a hundred-rule list is not read (BACKLOG #48).

**Every project** — Orcshot's tier: a desktop app, a phone app, a script — anything that runs
on a machine and talks only to services it chose. Rules 1–4.

**Reachable by strangers** — the tier of anything that accepts a connection from someone you did
not invite: an API on a web host, a site, a server a phone app talks to. Rules 1–4 and then
5–9 on top.

How Claude knows which: from the code when there is code (a route handler is a route handler;
a `main()` that opens a window is not); from `/orc-code`'s one question — *"Will anyone you
didn't invite be able to reach this?"* — when there is not yet any. The answer is not written
down anywhere: what the scaffold builds is the record, and from then on the code answers.

Applies whenever code is about to be written or changed, whoever started it — a `/orc-code`
scaffold, a subagent's task, a one-line fix in chat. Each rule says where it lands: **linted**
(a rule in the project's linter config, which `lint_on_write` runs on every write),
**scaffolded** (a piece `/orc-code` builds on day one), **`audit`** (`/orc-test audit`), or
**reviewed, not linted** (no tool checks it; Claude reads the code against the rule).

## 1. No secret in the repo or the built artifact — *Every project*

The situation: a password, an API key, a signing key or a token is about to be typed into a
source file, a config file that is committed, or anything that ends up inside the shipped app.
It goes in the platform's secret store or the environment instead, and the file that holds it
locally is in `.gitignore` before it exists. CWE-798 is *"Use of Hard-coded Credentials"*, and
its mitigation is to keep credentials *"outside of the code in a strongly-protected, encrypted
configuration file"*. ASVS 13.3.1 says the same for the build: secrets *"must not be included in
application source code or included in build artifacts."* OWASP's Mobile Top 10 puts it first,
M1: *"Always avoid using hardcoded credentials in your mobile app's code or configuration
files."* The `.git` directory is part of "the artifact" too — ASVS 13.4.1 wants a deployment
*"without any source control metadata, including the .git or .svn folders"*.

**Lands:** linted where the stack's tool has a hardcoded-secret rule (Python: ruff's
bandit-derived `S105`–`S107`, "hardcoded-password-*"; confirmed live 2026-09-19 against
ruff's rule index); scaffolded for the rest — the `.gitignore` entries and the platform's
secure store, named per stack in its `### Secrets` subsection. `secret-hygiene` covers the
transcript; this covers disk.

## 2. Dependencies audited against known vulnerabilities — *Every project*

The situation: the project depends on packages other people wrote, and one of them has a
published vulnerability. OWASP Top 10:2025 A03, Software Supply Chain Failures, lists the
failing as *"you do not scan for vulnerabilities regularly"*; ASVS 15.2.1: the application
*"only contains components which have not breached the documented update and remediation time
frames."* Orclab's time frame is: before anything reaches a remote.

**Lands:** **`audit`** — `/orc-test audit` runs each language's advisory check
(`skills/orc-test/languages/<lang>.md`, `## Audit`; Swift and GDScript have no free tool and
say so) and `/orc-git push`, `cp` and `release` run it before touching a remote. A
known-vulnerable dependency is a red gate with no skip flag.

## 3. Anything downloaded or run at runtime is verified first — *Every project*

The situation: the code fetches something over the network and then runs it, loads it, or
installs it — an auto-update, a plugin, a model file, a script — and nothing checks that what
arrived is what was expected. CWE-494, *"Download of Code Without Integrity Check"*: the product
*"executes the code without sufficiently verifying the origin and integrity of the code."*
OWASP A08 names the everyday case — *"updates are downloaded without sufficient integrity
verification"* — and the fix: *"Use digital signatures or similar mechanisms to verify the
software or data"*. A pinned checksum compared before use is the floor; a signature checked
against a key shipped with the app is the standard.

**Lands:** reviewed, not linted. No stack's tooling has a rule for "this bytes-to-exec path
had no check"; Claude reads every download-then-run path against this rule.

## 4. The app asks for the least permission it needs — *Every project*

The situation: a manifest, an entitlement list, a service account or a file mode is about to
grant more than the code uses — a whole-disk permission for one folder, a root account for one
table, a world-writable file. CWE-250, *"Execution with Unnecessary Privileges"*: *"Run your code
using the lowest privileges that are required"*. OWASP A02 counts *"unnecessary ports, services,
pages, accounts, testing frameworks, or privileges"* as misconfiguration; ASVS 13.2.2 wants
backend accounts *"assigned the least necessary privileges"*; Mobile M8 names the file case,
*"world-readable and/or world-writable permissions."*

**Lands:** scaffolded — `/orc-code` starts a project with no permissions declared and no
account beyond the one the app runs as; every addition is a diff someone can see. Reviewed,
not linted, after that: no stack's tooling checks whether a granted permission is used.

## 5. Every input that arrives over the network is hostile until validated — *Reachable by strangers*

The situation: a value came in on a request — a query parameter, a body field, a header, a
path, an uploaded file, a URL the caller supplied — and it is about to reach something that
interprets text: a SQL query, a shell, a file path, a template, a deserializer, an outbound
HTTP call. OWASP A05, Injection: an application is vulnerable when *"User-supplied data is not
validated, filtered, or sanitized by the application"*, and the fix is *"a safe API, which
avoids using the interpreter entirely, provides a parameterized interface"* plus *"positive
server-side input validation."* ASVS 2.2.1 says what validation is: *"positive validation
against an allow list of values, patterns, and ranges"*. The 2025 CWE Top 25 opens with this
rule's failures — #1 cross-site scripting, #2 SQL injection, #6 path traversal, #9 OS command
injection, #15 deserialization of untrusted data, #22 SSRF. Validation on the client does not
count (ASVS 2.2.2: *"it must not be relied upon as a security control"*).

**Lands:** two halves. Linted at the sink, where the stack's tool has the rule — Python:
ruff `S608` (hardcoded-sql-expression), `S602` (subprocess with `shell=True`), `S301`
(pickle), `S506` (unsafe yaml load); the stack section's `### Static analysis` names the
ruleset per language, or says "none free". Scaffolded at the door: every route has a
declared schema for its input, and a request that does not match is refused before the
handler runs. `test-discipline`'s trust-boundary line is the test of this rule.

## 6. Every route authenticates, unless it is deliberately public and says so in the code — *Reachable by strangers*

The situation: a new endpoint, page or handler is being added, and the question "who may call
this?" has not been answered in the code. OWASP A01, Broken Access Control: *"Except for public
resources, deny by default."* ASVS 8.2.1: *"function-level access is restricted to consumers
with explicit permissions."* CWE Top 25 2025 has this failure four times — #4 Missing
Authorization, #17 Incorrect Authorization, #21 Missing Authentication for Critical Function,
#24 Authorization Bypass Through User-Controlled Key (a record fetched by an id the caller
chose, without checking the caller owns it). "Says so in the code" means a public route is
public by an explicit marker or by living under the public directory — never by the absence
of a check.

**Lands:** scaffolded — `/orc-code` builds the auth layer and the public/private split on
day one for this tier, as that stack does it (the `### Reachable by strangers` subsection),
so a new route is private unless it is moved. Reviewed, not linted, for the ownership check
inside a handler.

## 7. An error never reaches the caller carrying internals — *Reachable by strangers*

The situation: something threw, and the framework's default is about to send the stack trace,
the failed query, a file path or a version string back over the wire. ASVS 16.5.1: *"a generic
message is returned to the consumer"* on any unexpected or security-sensitive error, naming *"stack traces, queries, secret keys, and tokens"* as what must not be in it. OWASP A02
counts *"Error handling reveals stack traces or other overly informative error messages"* as
misconfiguration; A10 wants *"a global exception handler in place"* for whatever was missed. The full detail goes to the log; the caller gets a generic message
and an id to quote. And the process fails closed: a validation error does not let the request
through (ASVS 16.5.3).

**Lands:** scaffolded — a last-resort exception handler that logs everything and returns
nothing but a generic message, and the framework's debug mode off outside development (ASVS
13.4.2). Neither `code-discipline`'s rule 6 (never swallow an error) nor this one is satisfied
by the other: log it fully, show it never.

## 8. Transport is encrypted and plain HTTP refused — *Reachable by strangers*

The situation: the app is about to listen on, or connect over, a channel that carries a
credential, a session or personal data. OWASP A04, Cryptographic Failures: *"Encrypt all data
in transit with protocols >= TLS 1.2 only"* and *"enforce encryption using HTTP Strict
Transport Security (HSTS)"*. ASVS 12.2.1: TLS *"does not fall back to insecure or unencrypted
communications."* The client side of the same rule is Mobile M5 — an app that accepts
*"bad ssl certificates (self-signed, revoked, expired, wrong host...)"* has no transport
security at all, and it is an every-project concern for any app that talks to a server, not only
for the server.

**Lands:** scaffolded at the server — the deploy configuration redirects or refuses plain HTTP
and sets HSTS, as the stack section says; linted at the client where the tool has the rule
(Python: ruff `S501`, request-with-no-cert-validation). Reviewed, not linted, everywhere else:
any code that turns certificate checking off is a finding.

## 9. Rate limits exist — *Reachable by strangers*

The situation: an endpoint can be called as fast as a script can call it — a login, a
password reset, a search, anything that costs the server more than it costs the caller. OWASP
A01: *"rate limits on API and controller access to minimize harm from automated attack
tooling."* A07 for the login case: *"Limit or increasingly delay failed login attempts"*.
ASVS 2.4.1 wants *"anti-automation controls"* against *"quota exhaustion, rate-limit breaches,
denial-of-service"*; CWE Top 25 2025 #25 is *"Allocation of Resources Without Limits or
Throttling"*. The limit on authentication routes is the one that is never optional.

**Lands:** scaffolded — a limiter in front of the auth routes at minimum, as the stack section
says; the number is the project's to tune, the presence is not. Reviewed, not linted, for the
routes added later.

## What this is not

- Not `secret-hygiene` — that keeps a credential out of the transcript; this keeps it out of the
  repo and the artifact, and points there for the rest.
- Not a penetration test, and not runtime protection.
- Not a memory-safety guide. Seven of the 2025 CWE Top 25 are buffer and pointer defects
  (out-of-bounds write and read, use after free, null dereference, the three overflows); none of
  Orclab's stacks is C, so they are the runtime's job and not a rule here.
- Not enforced by this file. The checkable rules are linter configuration — each `stack-*`
  skill's `## Security — where security-discipline lands` section — and Orclab's `lint_on_write`
  hook runs the project's configured linter on every write. The dependency rule is
  `/orc-test audit`, which `/orc-git` runs before anything reaches a remote. Bringing an
  existing codebase up to these rules is `/orc-code refactor`'s quality mode.

## Sources (live on 2026-09-19)

- OWASP Top 10:2025, the list — https://top10.owasp.org/2025/ (`https://owasp.org/Top10/`
  redirects here); category pages read: A01
  https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/, A02
  https://top10.owasp.org/2025/A02_2025-Security_Misconfiguration/, A03
  https://top10.owasp.org/2025/A03_2025-Software_Supply_Chain_Failures/, A04
  https://top10.owasp.org/2025/A04_2025-Cryptographic_Failures/, A05
  https://top10.owasp.org/2025/A05_2025-Injection/, A07
  https://top10.owasp.org/2025/A07_2025-Authentication_Failures/, A08
  https://top10.owasp.org/2025/A08_2025-Software_or_Data_Integrity_Failures/, A10
  https://top10.owasp.org/2025/A10_2025-Mishandling_of_Exceptional_Conditions/.
- OWASP ASVS 5.0.0 (May 2025) — the project page
  `https://owasp.org/www-project-application-security-verification-standard/` was a 404 on the
  day at every redirect target; the text was read from the tagged release,
  https://github.com/OWASP/ASVS (README names 5.0.0 as latest stable) and
  https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en — chapters V2 (validation), V4 (API), V6
  (authentication), V7 (session), V8 (authorization), V12 (secure communication), V13
  (configuration), V14 (data protection), V15 (secure coding), V16 (logging and error handling).
- 2025 CWE Top 25 — https://cwe.mitre.org/top25/ (landing) and
  https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html (the list).
- CWE entries — https://cwe.mitre.org/data/definitions/798.html (hard-coded credentials),
  https://cwe.mitre.org/data/definitions/494.html (download without integrity check),
  https://cwe.mitre.org/data/definitions/250.html (unnecessary privileges).
- OWASP Mobile Top 10 2024 — https://owasp.org/www-project-mobile-top-10/ (project page; its
  risk pages under `2023-risks/` were 404 on owasp.org on the day) and the same text at
  https://github.com/owasp/www-project-mobile-top-10/tree/master/2023-risks (index, M1, M5, M8).
- ruff's rule index, for the `S` rule names cited — https://docs.astral.sh/ruff/rules/.
