# Handoff: the first PHP project (DreamHost API for orcweather)

This is for a Claude Code session that has Orclab installed as a plugin and is working directly
on the new PHP API project — not on Orclab itself. You don't need to have read anything else;
everything you need is below.

## Start

Type `/orc-code` and answer its questions as they come, one at a time:

1. **Project name** — whatever you want to call it.
2. **App or game** — app.
3. **Platforms** — web only.
4. **Stack** — when `/orc-code` proposes a stack, say **PHP**. It's listed as an alternative
   choice on the web row, not the default, so you need to ask for it by name.
5. **Exposure** ("will anyone you didn't invite be able to reach this?") — **yes**. This is a
   public API that a phone app will call over the internet.
6. **Container** ("run this project's toolchain in a container?") — **yes**.
7. **Starting point** — **not** a minimal example. Instead describe your use case: a JSON API,
   on shared hosting (DreamHost), that another app (orcweather) will call.

Once the questions are answered, `/orc-code` will scaffold the project. Here is the toolchain it
should give you, so if something different shows up you'll recognize it as a surprise worth
asking about rather than assuming it's correct:

- **PHP 8.5** (8.5.10), running inside the container it sets up for you.
- **Composer 2.x** (2.10.3) as the dependency manager.
- **Slim 4** as the framework, with the `slim/psr7` package.
- **swagger-php** (`zircote/swagger-php`), which generates the API's OpenAPI contract document
  from PHP attributes on your route code — the command is `vendor/bin/openapi`.
- **PHPUnit** for tests.
- **Infection** for mutation testing (it should be run with the `--with-uncovered` flag so
  untested code counts against the score instead of being silently skipped).
- **PHPStan** for static analysis, set to its strictest level (`level: max`).
- **`composer audit --locked`** for checking dependencies against known security advisories.

## What Orclab could not verify and this session must record

Orclab researched this stack from documentation, but nobody has actually deployed a PHP project
to DreamHost's shared hosting through it yet — this is the first time. The following five things
are genuinely unknown and this is the session that finds out. As you go, write what you learn as
new numbered steps in this project's own `RELEASING.md` — use the `release-checklist` skill to
create or update it; don't write `RELEASING.md` by hand.

1. **Selecting PHP 8.5 for this domain in DreamHost's control panel.** DreamHost's panel is
   known to offer 8.5 as a choice per domain, but nobody has clicked through the actual screens
   yet. Record the exact steps.
2. **Installing Composer on the shared hosting account.** DreamHost has a support page with the
   steps for this; follow it and record what actually worked, including anything the page left
   out.
3. **What gets uploaded, and how.** Does `public/` become the web-visible document root? Is
   `vendor/` (the installed dependencies) built directly on the host, or built locally and
   uploaded? And is the upload itself done over SFTP, `git`, `rsync`, or something else? Record
   whatever you actually did.
4. **The `.env` file and PHP's error-display setting on the host.** The `.env` file (holding
   secrets like database passwords) must live above `public/`, where the web server can't serve
   it directly — never inside `public/`. Separately, PHP's `display_errors` setting needs to be
   off in production (DreamHost lets you override PHP settings with a `phprc` file) so errors
   aren't shown to visitors. Record where `.env` ended up and how you set `display_errors`.
5. **What the first deploy actually took.** Roughly how many minutes it took end to end, and any
   surprises or gotchas along the way.

When you're done, take those five recorded lines from your `RELEASING.md` and paste them into
Orclab's own backlog entry **#64** — through Orclab's `/orc-todo` command if it's available in
this session, or by hand otherwise. That entry currently has nothing in it but a placeholder;
these lines are its only real input, and they're what lets a future project's shared-hosting
deployment skip the guesswork you just did.

## The contract

Generate and commit the OpenAPI document the toolchain produces (`vendor/bin/openapi src -o
openapi.yaml`, or similar — check what `/orc-code` actually named it). Regenerate it any time a
route or its attributes change; don't let it go stale.

In this project's own README, say plainly where that file lives in the repository and the exact
command to regenerate it. This sentence matters beyond this project: another app, orcweather,
will call this API, and the README sentence is how a future session working on orcweather is
expected to find out what this API looks like — it has no other way to know.

If it later turns out that a plain README sentence isn't actually enough for orcweather's session
to find and use the contract — it can't locate the file, doesn't know which URL the API is
deployed at, or the contract has moved and nobody noticed — that gap is exactly what Orclab's
backlog entry **#65** is waiting to hear about. Report what specifically went wrong there.

## Report back

This is the first real PHP project Orclab has been used to build, so its PHP knowledge is
expected to have gaps or mistakes — that's normal, not a failure. As you go, if anything about
how PHP, Slim, Composer, or the container behaved turned out to be wrong or missing compared to
what Orclab told you to expect, write it down (referencing whatever section heading it was under)
and report it into Orclab's backlog entry **#50**. That's how the next PHP project benefits from
what this one actually ran into.
