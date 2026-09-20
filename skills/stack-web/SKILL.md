---
name: stack-web
description: Background knowledge for any work in a web project - a React front end built with Vite in TypeScript, served together with its API by a FastAPI back end in Python, and choosing the framework, the test runner or the storage mechanism for it. Says what the current toolchain is, where things live in the project, and how it is deployed. Not a command; Claude reads it when a web app is in play.
user-invocable: false
---

# Web — React (Vite) in front, FastAPI (Python) behind

No project has been built with this yet; the first one corrects it.

**Checked against live sources on 2026-09-12**; anything older than one release is suspect — re-check `## Sources`.

## When this is the stack

The `/orc-code` Defaults Table row **App / web only**: an application people open in a browser, at
a URL — nothing installed, nothing in a store. It has two halves: the page the browser runs (the front
end) and the program on a server that answers its requests and keeps its data (the back end). A web
app that only *talks to* a mobile app is two projects: the server is this stack, the phone client is
the mobile row's. Not this stack: a phone app's web build (`stack-react-native`'s `## React web and
desktop`), games (Godot, Unity), anything with a desktop or mobile target ticked.

## Toolchain, as of 2026-09-12

| Thing | Current | Where it was read |
|---|---|---|
| React | **19.3.0** (2026-09-09) | react.dev/versions; npm |
| Vite | **8.3.0** (2026-09-10); `create-vite` 9.2.1; *"Vite requires Node.js version 20.19+, 22.12+"* | npm; vite.dev/guide |
| TypeScript | the default — react.dev's own Vite command is `--template react-ts`; the template pins `typescript ~6.0.2` and lints with `oxlint` | react.dev; `create-vite/template-react-ts/package.json` on `main` |
| Node.js | LTS **24.21.0 "Krypton"** (2026-09-07) | nodejs.org release index |
| Vitest | **5.0.0** (2026-09-03); *"requires Vite >=v6.4.0 and Node >=v22.12.0"* | npm; vitest.dev/guide |
| FastAPI | **0.141.1** (2026-07-29); Python ≥ 3.10; `app.frontend()` since **0.138.0** (2026-06-20); SQLModel **0.0.42** (2026-08-28) on SQLAlchemy 2.0.52 | PyPI; fastapi.tiangolo.com/release-notes |
| Alternatives (below) | Next.js **16.3.5** (2026-09-11; Node ≥ 20.9); React Router **8.3.1** (2026-08-28); Django **6.1.1** (2026-09-02; Python 3.12–3.14) | npm; PyPI; docs.djangoproject.com/en/6.1/faq/install |

Install, each from its own page (confirmed live 2026-09-12): `npm create vite@latest web -- --template
react-ts` (react.dev's command, directory renamed); `pip install "fastapi[standard]"` in a venv (the
page's first form is `uv add`) — brings Uvicorn, HTTPX and the `fastapi` command; `pip install sqlmodel`.

## The stack decision

A web app's front end is the code the browser runs; React writes it as *components* — *"a piece of
the UI (user interface) that has its own logic and appearance"* (react.dev/learn). React is a library,
not a whole toolchain, so the choice is what wraps it.

**Front end: React with Vite, in TypeScript.** react.dev's start page says: *"If you want to build a
new app or website with React, we recommend starting with a framework"* and names Next.js first,
then React Router and Expo (react.dev/learn/creating-a-react-app, confirmed live 2026-09-12). This
skill departs from that on the page's own terms: its note *"Full-stack frameworks do not require a
server"* exists because those frameworks bring a Node server half — server rendering, server actions,
API routes — and the back end here is Python, so that half would sit unused. The from-scratch page's
warning is the concern that would reverse this: *"if in the future your app needs support for
server-side rendering (SSR), static site generation (SSG), and/or React Server Components (RSC), you
will have to implement those on your own."* An app behind an API needs none of those, and Vite is
the first tool that page names, with the one command `npm create vite@latest my-app -- --template
react-ts`. TypeScript is what react.dev types, so it is the default; `--template react` is plain
JavaScript. **Alternatives:** *Next.js (App Router)* — *"a React framework that takes full advantage
of React's architecture to enable full-stack React apps"*; concern that picks it: a content site that
must render on the server (SEO, first paint), or a Node back end (below). *React Router* — react.dev still
heads it "React Router (v7)" (confirmed live 2026-09-12) while npm's current release is 8.3.1, above —
*"can be paired with Vite to create a full-stack React framework"*; concern: react.dev's framework route
wanted on top of this skill's build tool. Both need a Node server unless statically exported.

**Back end: FastAPI.** The back end is the program that answers the browser's requests and owns the
data. The candidates are Python and Node, and the concern that decides it is Orclab's own: a Python
back end shares nothing with a React front end but keeps the developer in the language they already
know; a Node back end shares the language with the front end. By the selection rule — the easiest
option that works — Python wins because FastAPI's own docs show every piece of
this stack on a first-party page: serving the built React app (*"This is useful for frontend tools
that generate static files, like React with Vite"*, `app.frontend("/", directory="dist")`), the
database (*"SQLModel … was made by the same author of FastAPI to be the perfect match"*, SQLite in
the example) and tests (*"With it, you can use pytest directly with FastAPI"*) — one process serves both
halves. FastAPI is *"a modern, fast (high-performance), web framework for building APIs with Python
based on standard Python type hints"* (its front page). **Alternatives:** *Django 6.1* — *"Django
takes care of user authentication, content administration, site maps, RSS feeds, and many more tasks
— right out of the box"* (djangoproject.com/start/overview); concern that picks it: an admin screen
and user accounts on day one. Its docs show nothing about serving a React build (searched
docs.djangoproject.com, 2026-09-12: static-files pages only). *Next.js as the back end (Node)* — its
`route.ts` files are *"API endpoint"*s and `npm run build && npm run start` runs *"the Node.js
server"* (nextjs.org); concern that picks it: one language on both sides matters more than Python.
Its docs name no default database layer — *"an ORM or database client"*, a placeholder `@/lib/db`.

## Project layout — where things live

One repository, two directories. FastAPI's Frontend tutorial shows `pyproject.toml`, `app/main.py` and
`dist/` side by side but not where the front-end *source* lives; the Vite project in `web/`, and
`directory="web/dist"`, are Orclab's own placement — not from a page.

| Path | What |
|---|---|
| `pyproject.toml` | The Python project and its version — the file `/orc-version` writes. The front end's own `web/package.json` version it does not write (BACKLOG #6). |
| `app/main.py` | The FastAPI app: path operations, SQLModel tables and engine (`## Storage`), and `app.frontend("/", directory="web/dist")` last. |
| `tests/` | pytest, `test_*.py`, `TestClient(app)`. |
| `web/` | The Vite project: `index.html` at its root (*"the entry point to your application"*), `src/main.tsx`, `src/App.tsx`, `src/index.css`, `public/`, `vite.config.ts`, `tsconfig*.json`, `package.json` — the `react-ts` template's own files (confirmed live 2026-09-12). |
| `web/dist/` | `vite build`'s output — *"by default, the build output will be placed at `dist`"* — git-ignored by the template. What FastAPI serves. |

## Build, run, test

```bash
cd web && npm run dev                          # Vite dev server, http://localhost:5173, hot reload
fastapi dev app/main.py                        # the page's `fastapi dev`, this layout's path; API :8000, docs at /docs
cd web && npm run build                        # tsc -b && vite build -> web/dist/
fastapi run app/main.py                        # production: Uvicorn, one process, serves API + web/dist
cd web && npx vitest run && cd .. && python3 -m pytest -q   # tests, front then back (Orclab's own chaining)
```

In development the two servers run side by side; the browser talks to Vite, which forwards API calls
— `server.proxy`: *"Any requests whose request path starts with that key will be proxied to the
specified target"*, its example key being `'/api'`. Put the API under `/api/...` and set
`proxy: { '/api': { target: 'http://localhost:8000' } }` in `web/vite.config.ts` (the docs' example
with FastAPI's port). In production there is one server: *"FastAPI checks path operations first. The
frontend files are checked only if no normal route matched"*; an unknown path gets `index.html`
(`fallback="auto"`), so client-side routing works; `check_dir="auto"`: *"When the `FASTAPI_ENV`
environment variable is set to `development`, FastAPI only shows a warning if the frontend build
output directory is missing … In any other environment, FastAPI raises an error when the app is
created"* — `fastapi dev` sets `FASTAPI_ENV=development` for you if it isn't already set.

Tests: Vitest — *"a next generation testing framework powered by Vite"*, reading `vite.config.*`;
pytest with FastAPI's `TestClient` (*"the testing functions are normal `def`, not `async def`"*).
Coverage, mutation and test lint: `skills/orc-test/languages/javascript.md` and `python.md`.

## Lint — where code-discipline lands

The template ships `.oxlintrc.json` and `npm run lint` is `oxlint` (oxlint 1.82.0; the three rules
are its ports of ESLint's, confirmed 2026-09-13 in `oxc_linter/src/rules/eslint/`). Add:

```json
"rules": {
  "max-depth": ["error", { "max": 2 }],
  "max-lines-per-function": ["error", { "max": 60, "skipBlankLines": true, "skipComments": true }],
  "no-empty": ["error", { "allowEmptyCatch": false }]
}
```

ESLint's own defaults, which oxlint mirrors: `max-depth` 4, `max-lines-per-function` 50, and
`no-empty` exempts a `catch` that *"contains a comment"* — that exemption is `code-discipline`
rule 6's "named, commented suppression", so keep it; `allowEmptyCatch: false` only refuses the
*uncommented* one. Every rule at `"error"` — a linter has no separate warnings-as-errors switch,
and `oxlint --deny-warnings` is the CLI form. TypeScript has errors only; `"strict": true` in
`tsconfig` is already set by the template. Rules 2, 3 and 5 are reviewed, not linted.

### The FastAPI back end

The same rules for the Python half, in `pyproject.toml` — confirmed 2026-09-13 against ruff
0.16.7's and pyright 1.1.414's own docs:

```toml
[tool.ruff]
preview = true                      # PLR1702 has been a preview rule since 0.1.15
[tool.ruff.lint]
extend-select = ["PLR1702", "PLR0915", "E722", "S"]   # "S" is the security ruleset — see Security below
[tool.ruff.lint.pylint]
max-nested-blocks = 2               # ruff's default is 5
max-statements = 50                 # ruff's default; statements, not lines — about a printed page
[tool.pyright]
typeCheckingMode = "strict"         # default is "standard"
```

`PLR1702` too-many-nested-blocks, `PLR0915` too-many-statements, `E722` bare-except (on by
default), and inside `S`, `S110` try-except-pass (*"consider logging the exception"*) — the
rule this section needs; the rest of `S` is the Security section's. These sit on top of ruff's
own default set, which since 0.16 is **five whole categories** — *"correctness, suspicious,
complexity, performance, style"*, about 800 rules (its linter doc, confirmed live 2026-09-13) —
not the old `E4/E7/E9/F` handful; the first run on an existing codebase says so loudly (Orclab's
own: 190 findings, 146 of them from those defaults, all fixed the same day). Python has no compiler
warnings: ruff and pyright *are* the analyzer, both exit non-zero on a finding, and that is the
warnings-as-errors switch; `python -W error` in the test command promotes the runtime
`DeprecationWarning`s. Rules 2, 3 and 5 (loop exits, closing on the error path, checks that
survive release) have no linter — they are reviewed, not linted.

## Security — where security-discipline lands

`security-discipline`'s rules for this stack, confirmed live 2026-09-19;
no project has been through this yet, and the first one corrects it. This stack is the
*Reachable by strangers* tier by definition — a web app is at a URL — so all nine rules
apply, and the four subsections below say where each lands in the two halves.

### Static analysis

**The browser half: oxlint has no security plugin, and the ESLint one is not worth a second
linter.** oxlint's rule tree (`oxc_linter/src/rules/`, 16 directories, read live 2026-09-19)
has no `security` directory. `eslint-plugin-security` 4.0.1 (2026-06-12, Apache-2.0) exists
on npm with fifteen rules, and its README's own verdict is *"finds a lot of false positives
which need triage by a human."* Eight of the fifteen are Node-only (`child_process`, `fs`
filenames, `require`, `new Buffer` and `noAssert`, Express CSRF middleware,
`pseudoRandomBytes`, template-engine escaping) and cannot fire on `web/`. Of the seven that
could, one is covered: `detect-eval-with-expression` is oxlint's `no-eval` (`correctness`, on
by default; `no-implied-eval` and `no-new-func` beside it). The other six are **reviewed, not
linted**: `detect-unsafe-regex` and `detect-non-literal-regexp` (a regex that runs for ever
— oxlint's `no-invalid-regexp`, `no-control-regex` and `no-misleading-character-class` check
a regex's validity, not its run time); `detect-bidi-characters` and
`detect-invisible-characters` (hidden Unicode in source —
oxlint's `no-irregular-whitespace` is whitespace only); `detect-object-injection`
(`obj[key]`, which is every ordinary lookup in a React app); `detect-possible-timing-attacks`
(the browser compares no secret — the password check is the server's, in `pwdlib`). Running
ESLint for one covered rule and six the README says need a human is the second linter for
nothing, so it does not run here.

What the browser half owes on its own is rule 5's XSS half — CWE Top 25 #1 — at the point
where a value is used. react.dev marks exactly one prop as the way to put raw HTML on the
page, `dangerouslySetInnerHTML`: *"Unless the markup is coming from a completely trusted
source, it is trivial to introduce an XSS vulnerability this way"*; the other way is a
`javascript:` URL in an `href`. oxlint ports both of React's rules (`no_danger.rs`,
`jsx_no_script_url.rs`, in the `react` directory the template already enables); `no-danger`
is in oxlint's `restriction` category and `jsx-no-script-url` in `suspicious`, neither on by
default (only `correctness` is). JSON does not merge, so the `.oxlintrc.json` `rules` object
is written once — the Lint section's three entries plus these two:

```json
"rules": {
  "max-depth": ["error", { "max": 2 }],
  "max-lines-per-function": ["error", { "max": 60, "skipBlankLines": true, "skipComments": true }],
  "no-empty": ["error", { "allowEmptyCatch": false }],
  "react/no-danger": "error",
  "react/jsx-no-script-url": "error"
}
```

`no-danger`: *"`dangerouslySetInnerHTML` is a way to inject HTML into your React component.
This is dangerous because it can easily lead to XSS vulnerabilities."* `jsx-no-script-url`:
*"URLs starting with `javascript:` are a dangerous attack surface because it's easy to
accidentally include unsanitized output in a tag like `<a href>`."* A component that must
render HTML sanitises it first and suppresses `no-danger` on that one line with the reason —
`code-discipline`'s named, commented suppression. (Confirmed live 2026-09-19: oxlint 1.83.0 on
npm, `eslint-plugin-security` on npm and its README, the `.rs` files named above and oxlint's
config page, react.dev's common-components reference; and run — oxlint 1.83.0 via `npx` on a
three-line fixture with the template's `.oxlintrc.json` plus the two rules: both fire as
errors, and `eval("1")` fires as a `no-eval` warning with nothing added, which
`--deny-warnings` turns red.)

**The FastAPI half** gets ruff's `S` category — its port of bandit, 71 live rules (73 listed,
`S320` and `S410` marked removed) — every code `security-discipline` cites among them: rule
1's `S105`–`S107` hardcoded password, rule 5's `S608` SQL built from strings, `S602`
`shell=True`, `S301` pickle, `S506` unsafe `yaml.load`, rule 8's `S501` `verify=False`; plus
the ones only a server trips, `S104` (bind to all interfaces in code) and `S701` (Jinja2 with
autoescape off). The whole category, so the skill's codes are a subset and cannot drift: the
`"S"` in the `extend-select` line of the Lint section's `### The FastAPI back end` block is
this. Two more lines go inside the `[tool.ruff.lint]` table the Lint section already opens
(ruff 0.16.8, 2026-09-16; confirmed live 2026-09-19 against its rule index and settings page,
and run on 0.16.8 against a five-line fixture: `S105` fires, `S101` in `tests/` does not,
`S403`/`S404` fire only when the `ignore` line is removed):

```toml
ignore = ["S4"]                     # the 13 "suspicious import" rules: the call-site rules already cover them
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]               # assert is the test framework's own statement
```

`S101` (*"Use of `assert` detected"*) stays on for `app/` — assertions *"are removed when
Python is run with optimization requested"*, `code-discipline` rule 5's reason — and off for
`tests/`, which pytest builds on `assert`; the rule page has no test exemption of its own.
`S401`–`S415` flag an `import` rather than a call, are preview rules that the Lint section's
`preview = true` would switch on, and duplicate the call-site rules, hence the `ignore`.
`S603` (*"Prone to false positives"*, its own page) and `S607` (partial executable path) are
the noisy ones a server rarely hits; a hit gets the full path or a per-line `# noqa: S603`
with the reason. pyright has no
security rules (its configuration reference, read 2026-09-13). Rules 3, 4, 6's ownership check
and 9's later routes have no linter — reviewed, not linted.

### Dependency audit

Two languages, two runs, both from `/orc-test audit`: `npm audit --json` on `web/`'s lock file
— `skills/orc-test/languages/javascript.md`, `## Audit`; npm ships with Node — and pip-audit on
`pyproject.toml`'s declared dependencies — `languages/python.md`, `## Audit`;
`pip install pip-audit` (rule 2).

### Secrets

**Server:** every secret — the JWT signing key, a database URL with a password in it, an API
key for a service the back end calls — is an environment variable, read once through
`pydantic-settings` 2.15.0 (2026-08-07, MIT, Python ≥ 3.10; confirmed live 2026-09-19 on PyPI
and FastAPI's settings page). A `Settings(BaseSettings)` class in `app/config.py` with a field
per secret and `model_config = SettingsConfigDict(env_file=".env")` reads the process
environment and a local `.env` file, and a `@lru_cache`'d `get_settings()`
dependency hands it to routes — FastAPI's own page's shape. `.env` is in `.gitignore` before
it exists. The JWT tutorial's `SECRET_KEY = "09d25e…"` on one line of `main.py` is the exact
thing ruff's `S105` flags and rule 1 forbids; the scaffold has `secret_key: str` in `Settings`
instead, populated from `openssl rand -hex 32` — the tutorial's own command, with its warning:
*"don't use the one in the example"*. **Browser: nothing secret ever in `web/`.** Vite's own
page: *"`VITE_*` variables should not contain sensitive information such as API keys. The
values of these variables are bundled into your source code at build time"* — `web/dist` is
served to everyone who asks, so anything in it is public by construction, and a key the front
end needs is a route on the back end that holds the key and answers on the user's behalf.
Vite's `*.local` env files are the local-only kind, and the template's own `_gitignore`
already carries `*.local` but not `.env`; the repository root's `.gitignore` gets `.env`
(confirmed live 2026-09-19: `vite.dev/guide/env-and-mode` and the template's `_gitignore`).
Never in the built artifact: `.env`, `*.local`, and `.git` —
the deployed unit is `web/dist` plus the Python package, not the repository (rule 1).

### Reachable by strangers

What `/orc-code` scaffolds on day one for this tier, each piece from FastAPI's own pages
(confirmed live 2026-09-19):

- **Auth (rule 6):** the security tutorial's fourth page, *OAuth2 with Password (and hashing),
  Bearer with JWT tokens* — `pyjwt` 2.14.0 (2026-09-11) for the token, `pwdlib[argon2]` 0.3.1
  (2026-08-12) for the password hash, a `/token` route that issues a bearer token, and a
  `get_current_user` dependency that decodes it and raises `401` (*"Could not validate
  credentials"*) on anything invalid. **The public/private split:** private routes live on an
  `APIRouter(dependencies=[Depends(get_current_user)])` — the bigger-applications page: *"All
  these path operations will have the list of dependencies evaluated/executed before them"* —
  so a new route on that router is authenticated by being there, and a public route is public
  by living on the second router, the one with no dependencies — the split is which file the
  route is in, with nothing to forget. `app.frontend()` serves
  `web/dist` to anyone; that is the site, not the API. The ownership check inside a handler
  (the record's owner is the caller) is reviewed, not scaffolded.
- **Input (rule 5):** FastAPI's door is already the declared schema — a route's parameters and
  its Pydantic body model are the allow-list, and a request that does not match gets `422`
  before the handler runs (the handling-errors page: *"When a request contains invalid data,
  FastAPI internally raises a `RequestValidationError`"*). What the scaffold adds is the rule
  that every body is a model with typed, bounded fields — no `dict`, no `Any` — and that a
  query is written the way the SQL tutorial writes it, `session.get(Hero, hero_id)` or
  `select(Hero).where(...)`, never as a string with the value inside; `S608` catches the
  string-built one.
- **Errors (rule 7):** a last-resort handler, `@app.exception_handler(Exception)` (Starlette:
  *"Both keys `500` and `Exception` can be used"*), that logs the full traceback with a
  generated id and returns `{"error": "internal error", "id": …}` and nothing else. Two
  defaults to know: `FastAPI(debug=…)` is `False` by default — *"Boolean indicating if debug
  tracebacks should be returned on server errors"* — and stays so; and the default `422`
  body names the field and what was wrong with it (`loc`, `msg`, `type` — the page's
  example) and nothing about the server, which is what a form needs; override it
  (`@app.exception_handler(RequestValidationError)`, same page) only if a field name is
  itself private. The `HTTPException` detail strings the auth layer raises are written for
  the caller, so they carry nothing.
- **Transport (rule 8):** the `## Deployment` section already puts a reverse proxy in front
  holding the certificate — FastAPI's HTTPS page: *"a separate system to handle HTTPS with a
  TLS Termination Proxy instead of just using the TLS certificates with the application
  server directly"* — so the redirect from `http://` and the HSTS header are that proxy's
  configuration, not the app's; the page does not mention HSTS (checked), so it is written
  into the proxy config the scaffold leaves, per proxy, on the first project. When the app
  must terminate TLS itself, FastAPI's `HTTPSRedirectMiddleware` (*"Any incoming request to
  `http` or `ws` will be redirected to the secure scheme"*) and `TrustedHostMiddleware`
  (`allowed_hosts=[...]`, *"to guard against HTTP Host Header attacks"*) are on its middleware
  page. The browser side: `fetch` to the same origin over the page's own HTTPS — nothing to
  configure.
- **Rate limits (rule 9):** FastAPI has none built in — its features page and its security
  tutorial name no limiter (read 2026-09-19). `slowapi` 0.1.10
  (2026-06-13, MIT; confirmed live 2026-09-19 on PyPI and its docs) is the Starlette/FastAPI
  extension: `limiter = Limiter(key_func=get_remote_address)`, `app.state.limiter = limiter`,
  `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)`, then
  `@limiter.limit("5/minute")` under the route decorator (*"the route decorator must be above
  the limit decorator"*), on a handler that declares `request: Request` — its README: *"The
  `request` argument must be explicitly passed to your endpoint, or slowapi won't be able to
  hook into it."* The scaffold puts it on `/token`; the number is the project's.

## Containers

Runs in a container: **yes** — confirmed live 2026-09-20. Both halves' tests, every `/orc-test`
step in both languages, `lint_on_write` and `vite build` run inside; what does not is the two
dev servers, which bind ports the `compose.yaml` does not publish.

**One image, one service.** `/orc-test` runs one service named `orclab` for every language it
finds, so both toolchains live in one image. Node goes into the Python image rather than the
other way round because the Python version is the tighter one — the toolchain table names
3.14.7, and `python:3.14` *is* 3.14.7 — while any Node ≥ 22.12 satisfies Vite, Vitest and
StrykerJS. How Node gets in, from primary sources. The official `node` image's Dockerfile
downloads the release tarball from nodejs.org, checks its SHA-256 against the GPG-signed
`SHASUMS256.txt`, and unpacks it into `/usr/local`. What lands there is the tarball's own
layout, listed from `node-v24.21.0-linux-x64.tar.xz` on this machine: `bin/node`,
`lib/node_modules/{npm,corepack}`, and `bin/npm` and `bin/npx` as symlinks into it. A build
stage from that image and `COPY --from` carries the verified binary over. Docker: *"The `COPY
--from` flag lets you copy files from an image, a build stage, or a named context"*; Podman's
Containerfile: *"copy files from a named previous build stage"* — so the stage is named, the
form both engines document.
`node:24-trixie` is Node 24.21.0 LTS "Krypton" on the same Debian trixie as `python:3.14`,
so the binary meets the C library it was built against. NodeSource's apt repository is the
other route; its own README lists Debian only up to 12 bookworm, and it is a downloaded
script run as root — `security-discipline` rule 3's shape — so not this one.

The `Dockerfile` `/orc-code` writes when the user says yes to the container question — base
image and tag from the official `python` and `node` images' own tag lists, the two toolchains,
and every tool `skills/orc-test/languages/python.md` names (pytest, pytest-cov, mutmut,
pip-audit) plus ruff, which `lint_on_write` runs:

```dockerfile
FROM node:24-trixie AS nodejs
FROM python:3.14
COPY --from=nodejs /usr/local/bin/node /usr/local/bin/node
COPY --from=nodejs /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
RUN pip install --no-cache-dir "fastapi[standard]" sqlmodel pytest pytest-cov mutmut pip-audit ruff
```

Not run here — the first project records it. `python:3.14`, not `-slim`, for the reason
`stack-python-desktop`'s Containers section gives (the README's own recommendation, and
`buildpack-deps`' compiler for any wheel that needs building). The `pip install` line is each
tool's own documented install (PyPI today: pytest 9.1.1, pytest-cov 7.1.0, mutmut 3.8.0,
pip-audit 2.10.1, ruff 0.16.8), plus the back end's two dependencies from `## Toolchain`,
because the image is where the Python dependencies live — `compose run --rm` discards the
container after every command, so a `pip install` inside it is gone by the next one; a
dependency added to `pyproject.toml` goes on this line too, then `<engine> compose build
orclab` — the same rebuild picks up a new tool version, since the line is unpinned.
`/usr/local/include/node` is not copied: only a native addon build needs it, and this
stack has none.

**Which JS tools the image installs: none.** They are the project's own `devDependencies` in
`web/package.json`, installed into `web/node_modules` — inside the mounted tree, so they
survive the container and are the same files the host sees. `oxlint` is in the `react-ts`
template already (`^1.83.0`, its `package.json` on `main`); `vitest` 5.0.1,
`@vitest/coverage-v8` 5.0.1, `@stryker-mutator/core` 10.0.0 and
`@stryker-mutator/vitest-runner` 10.0.0 are added by the project (`languages/javascript.md`
picks Vitest when `vitest` is in `package.json`). `npm audit` and `npx` ship with npm, which
came over with Node. The one command that installs anything is the project's own `npm
install`, run through the container once — `<engine> compose run --rm --workdir $PWD/web
orclab npm install` from the project root — and again when `package.json` changes;
`lint_on_write` then finds `web/node_modules/.bin/oxlint` by path. Host and container are both
`linux-x64-gnu`, so oxlint's platform binary package is the same either side. Vitest 5.0.1
wants Node `^22.12.0 || ^24.0.0 || >=26.0.0`, Stryker `>=22.0.0`, oxlint `^20.19.0 ||
>=22.12.0` (each package's `engines` on the npm registry today): 24.21.0 satisfies all three.

The `compose.yaml` is the one in `skills/orc-test/SKILL.md`'s Containers section, unchanged.
What cannot happen inside: reaching `npm run dev` (:5173) or `fastapi dev` (:8000) from a
browser — the compose file publishes no port, so the dev loop is the host's, on a host venv
and `node_modules` as `## Build, run, test` shows, or a `ports:` line the first project adds
and records. The container is a development environment, not what ships: `## Deployment` is
unchanged, and a production image is a separate, deferred BACKLOG entry. The proposal
`/orc-code` makes for this stack's container question: **no**, because Node and Python are
the two toolchains most likely already on a dev machine, and each half's install is one
command from `## Toolchain`; say yes when the machine's Node is below 22.12 or its Python
below 3.10 and neither is yours to upgrade.

## Presence

Presence is how the app reaches the person when its tab is not in front — or is closed. A web page
cannot draw a tray icon; what it has is the operating system's own notification. The Notifications API
*"allows web pages to control the display of system notifications to the end user"*; they *"are
rendered by the operating system's native notification system"* and *"can be shown even when the user
has switched tabs or moved to a different app"* — after `Notification.requestPermission()`, over HTTPS
only (MDN, 2026-05-25; confirmed live 2026-09-12). That reaches an open tab. To reach a closed one the
app registers a *service worker* — a script the browser keeps — and the server sends a push: *"The
Push API gives web applications the ability to receive messages pushed to them from a server, whether
or not the web app is in the foreground, or even currently loaded"* (MDN; Baseline since March 2023);
the worker shows it with `ServiceWorkerRegistration.showNotification()`, and the sending side is a
FastAPI route holding each browser's `PushSubscription`.

A PWA is the same site with a manifest and that service worker, which the browser can then install:
*"an app that's built using web platform technologies, but that provides a user experience like that
of a platform-specific app"* — an icon alongside native apps, its own window, offline operation, push,
*"a badge on the app icon"* (MDN, 2025-12-04). Desktop and Android give it a window and a launcher
entry; on iOS push works only once the site is on the Home Screen — *"with iOS and iPadOS 16.4, we
are adding support for Web Push to Home Screen web apps"* (webkit.org, 2023-02-16).

## UI

The UI is React components, composed the way react.dev's *Thinking in React* shows: *"you will first
break it apart into pieces called components … describe the different visual states for each … then
connect your components together so that the data flows through them"*, data flowing down as props
(*"one-way data flow"*). Styling: react.dev names no CSS strategy — *"React does not prescribe how you
add CSS files"*; its example is a `className` and a plain `.css` file, which is what Vite's template
ships (`src/index.css`, `src/App.css`). BACKLOG #2's design system translates into the frameworks above.

## Storage

Storage is what the app keeps: records on the server, and small things in the browser.
**Server side: SQLite via SQLModel**, FastAPI's own recommendation — *"SQLite is used because it uses
a single file and Python has integrated support"* (its SQL tutorial); `create_engine("sqlite:///
database.db", connect_args={"check_same_thread": False})`, the second argument *"necessary since a
single request could use more than one thread"*. Right for one host serving one process. Concern that
picks **PostgreSQL** (any SQLAlchemy database is a URL change), from the same page — *"For production
applications, you might want to use a database server like PostgreSQL"* — i.e. more than one process
or host writing at once (Django's tutorial says the same). **Browser side:** `localStorage` — *"it
persists even when the browser is closed and reopened"*, per origin — for settings and a draft;
IndexedDB — *"client-side storage of significant amounts of structured data, including files/blobs"*
— for anything larger or offline (MDN, confirmed live 2026-09-12). External databases are out of scope.

## Deployment

There is no store and no review: a web app is deployed by running it somewhere with a hostname, so
no `orc-package` ingredient exists for this row, and this section replaces "where each store rule
lands". The unit is one Python process — `fastapi run` starts *"a production server, Uvicorn"* —
serving `web/dist` and the API on one port; FastAPI's deployment page lists what is still yours:
*"Security - HTTPS, Running on startup, Restarts, Replication"*, i.e. a reverse proxy holding the
certificate, and a service manager. Static hosting — Vite: *"You may deploy this `dist` folder to any
of your preferred platforms"* (GitHub Pages, Netlify, Cloudflare, …) — is only for a front end with no
back end, or whose API is at another origin (then CORS is the back end's job). Shipping a
container is deliberately parked (v18 spec §6, still so under v23); no default here —
`## Containers` above is the development environment, not the deployed unit.

## Sources (live on 2026-09-12)

- Lint — where code-discipline lands (2026-09-13): `https://raw.githubusercontent.com/oxc-project/oxc/main/crates/oxc_linter/src/rules/eslint/{max_depth,max_lines_per_function,no_empty}.rs`, `.../apps/oxlint/src/command/lint.rs` (`--deny-warnings`), `https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/_oxlintrc.json`; ESLint defaults `https://raw.githubusercontent.com/eslint/eslint/main/docs/src/rules/{max-depth,max-lines-per-function,no-empty}.md`; `https://docs.astral.sh/ruff/rules/`, `https://docs.astral.sh/ruff/settings/`, `https://raw.githubusercontent.com/microsoft/pyright/main/docs/configuration.md`; versions from `https://pypi.org/pypi/<name>/json`
- Security — where security-discipline lands (2026-09-19): `https://api.github.com/repos/oxc-project/oxc/contents/crates/oxc_linter/src/rules` (no `security/`), `.../rules/react`, `.../rules/eslint`; `https://raw.githubusercontent.com/oxc-project/oxc/main/crates/oxc_linter/src/rules/react/{no_danger,jsx_no_script_url}.rs`, `.../eslint/no_eval.rs`; `https://oxc.rs/docs/guide/usage/linter/config.html` (categories; `correctness` is the default), `https://oxc.rs/docs/guide/usage/linter/rules/react/no-danger.html`; `https://react.dev/reference/react-dom/components/common` (`dangerouslySetInnerHTML`); `https://registry.npmjs.org/eslint-plugin-security`, `https://raw.githubusercontent.com/eslint-community/eslint-plugin-security/main/README.md`, `https://registry.npmjs.org/oxlint`; `https://docs.astral.sh/ruff/rules/` (the flake8-bandit table), `.../rules/assert/`, `.../rules/subprocess-without-shell-equals-true/`, `https://docs.astral.sh/ruff/settings/`; `https://vite.dev/guide/env-and-mode`, `https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/_gitignore`; FastAPI `https://fastapi.tiangolo.com/tutorial/security/`, `/tutorial/security/oauth2-jwt/`, `/tutorial/bigger-applications/`, `/tutorial/handling-errors/`, `/advanced/settings/`, `/advanced/middleware/`, `/deployment/https/`, `/features/`, `/reference/fastapi/` (`debug`); `https://starlette.dev/exceptions/`; `https://slowapi.readthedocs.io/en/latest/`, `https://raw.githubusercontent.com/laurents/slowapi/master/README.md`; versions from `https://pypi.org/pypi/<name>/json` for `ruff`, `pydantic-settings`, `pyjwt`, `pwdlib`, `slowapi`; the fixture runs: ruff 0.16.8 in a scratch venv and `npx oxlint@1.83.0`, on this machine
- Containers (2026-09-20): tags `https://raw.githubusercontent.com/docker-library/official-images/master/library/python` and `.../library/node`; `https://raw.githubusercontent.com/docker-library/docs/master/python/README.md`, `.../node/README.md` (variants); `https://raw.githubusercontent.com/nodejs/docker-node/main/24/trixie/Dockerfile` (GPG-checked `SHASUMS256.txt`, `tar -xJf … -C /usr/local --strip-components=1`); the tarball's layout: `https://nodejs.org/dist/v24.21.0/node-v24.21.0-linux-x64.tar.xz` listed with `tar -t` on this machine; `https://nodejs.org/dist/index.json` (24.21.0 is LTS "Krypton"); `https://docs.docker.com/reference/dockerfile/#copy---from`; `https://raw.githubusercontent.com/containers/common/main/docs/Containerfile.5.md` (`COPY --from=name`); NodeSource `https://raw.githubusercontent.com/nodesource/distributions/master/DEV_README.md` (DEB supported versions, the setup script); `https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/package.json` (`oxlint` in `devDependencies`); `engines` and versions from `https://registry.npmjs.org/<pkg>` for `vitest`, `@vitest/coverage-v8`, `@stryker-mutator/core`, `@stryker-mutator/vitest-runner`, `oxlint`; the Python lines' sources are in `stack-python-desktop`'s Containers entry (pytest, pytest-cov, mutmut, pip-audit, ruff install pages; `https://pypi.org/pypi/<name>/json`)
- Versions: `https://registry.npmjs.org/<pkg>` for `react`, `vite`, `create-vite`, `vitest`, `next`, `react-router`, `jest`; `https://nodejs.org/dist/index.json`; `https://pypi.org/pypi/<pkg>/json` for `fastapi`, `django`, `uvicorn`, `sqlmodel`, `sqlalchemy`, `pytest`; `https://www.python.org/downloads/`; `https://react.dev/versions`
- React: `https://react.dev/learn/creating-a-react-app`, `/learn/build-a-react-app-from-scratch`, `/learn` (Quick Start), `/learn/thinking-in-react`
- Vite: `https://vite.dev/guide/`, `/config/server-options`, `/guide/static-deploy`; template files via `https://api.github.com/repos/vitejs/vite/contents/packages/create-vite/template-react-ts` and `https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/{package.json,_gitignore}`; `https://vitest.dev/guide/`
- FastAPI: `https://fastapi.tiangolo.com/`, `/tutorial/frontend/`, `/tutorial/static-files/`, `/tutorial/sql-databases/`, `/tutorial/testing/`, `/deployment/manually/`, `/release-notes/`
- Alternatives: `https://nextjs.org/docs/app/getting-started/installation`, `/docs/app/getting-started/project-structure`, `/docs/app/getting-started/fetching-data`, `/docs/app/getting-started/deploying`, `/docs/app/guides/static-exports`, `/docs/app/guides/testing`; `https://reactrouter.com/start/framework/installation`; `https://www.djangoproject.com/`, `/start/overview/`, `https://docs.djangoproject.com/en/6.1/intro/tutorial02/`, `/en/6.1/faq/install/`, and a site search of `docs.djangoproject.com` for a React/SPA page (none)
- MDN and WebKit: `https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API`, `/Web/API/Push_API`, `/Web/Progressive_web_apps/Guides/What_is_a_progressive_web_app`, `/Web/API/Web_Storage_API`, `/Web/API/IndexedDB_API`; `https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/`
