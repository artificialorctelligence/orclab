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
must render on the server (SEO, first paint), or a Node back end (below). *React Router v7* — *"can
be paired with Vite to create a full-stack React framework"*; concern: react.dev's framework route
wanted on top of this skill's build tool. Both need a Node server unless statically exported.

**Back end: FastAPI.** The back end is the program that answers the browser's requests and owns the
data. The candidates are Python and Node, and the one concern that decides between them is stated in
Orclab's own spec: *a Python back end shares nothing with a React front end but keeps direflail in
the language they know; a Node back end shares the language with the front end.* By the selection
rule — the easiest option that works — Python wins because FastAPI's own docs show every piece of
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
back end, or whose API is at another origin (then CORS is the back end's job). Containers (Docker)
are BACKLOG #4's open exploration, not decided here.

## Sources (live on 2026-09-12)

- Versions: `https://registry.npmjs.org/<pkg>` for `react`, `vite`, `create-vite`, `vitest`, `next`, `react-router`, `jest`; `https://nodejs.org/dist/index.json`; `https://pypi.org/pypi/<pkg>/json` for `fastapi`, `django`, `uvicorn`, `sqlmodel`, `sqlalchemy`, `pytest`; `https://www.python.org/downloads/`; `https://react.dev/versions`
- React: `https://react.dev/learn/creating-a-react-app`, `/learn/build-a-react-app-from-scratch`, `/learn` (Quick Start), `/learn/thinking-in-react`
- Vite: `https://vite.dev/guide/`, `/config/server-options`, `/guide/static-deploy`; template files via `https://api.github.com/repos/vitejs/vite/contents/packages/create-vite/template-react-ts` and `https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/{package.json,_gitignore}`; `https://vitest.dev/guide/`
- FastAPI: `https://fastapi.tiangolo.com/`, `/tutorial/frontend/`, `/tutorial/static-files/`, `/tutorial/sql-databases/`, `/tutorial/testing/`, `/deployment/manually/`, `/release-notes/`
- Alternatives: `https://nextjs.org/docs/app/getting-started/installation`, `/docs/app/getting-started/project-structure`, `/docs/app/getting-started/fetching-data`, `/docs/app/getting-started/deploying`, `/docs/app/guides/static-exports`, `/docs/app/guides/testing`; `https://reactrouter.com/start/framework/installation`; `https://www.djangoproject.com/`, `/start/overview/`, `https://docs.djangoproject.com/en/6.1/intro/tutorial02/`, `/en/6.1/faq/install/`, and a site search of `docs.djangoproject.com` for a React/SPA page (none)
- MDN and WebKit: `https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API`, `/Web/API/Push_API`, `/Web/Progressive_web_apps/Guides/What_is_a_progressive_web_app`, `/Web/API/Web_Storage_API`, `/Web/API/IndexedDB_API`; `https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/`
