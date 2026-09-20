---
name: stack-php
description: Background knowledge for any work in a PHP web back end - an API alone, behind a React front end from stack-web, or serving HTML itself; creating one, running its tests, coverage and mutation testing, auditing its dependencies, containerising its toolchain, or preparing it for a host that serves PHP and nothing else. Says what the current toolchain is, where things live in the project, and what is not yet known about shared-hosting deployment. Not a command; Claude reads it when PHP is in play.
user-invocable: false
---

# PHP — a web back end

No project has been built with this yet; the first one corrects it. Unlike the other stack
skills, every command below was run in a container on the machine that wrote it (2026-09-20),
so "not run here" appears only in `## Deployment`.

**Checked against live sources on 2026-09-20**; anything older than one release is suspect — re-check `## Sources`.

## Toolchain, as of 2026-09-20

Every version here is what the tool itself printed inside the image on 2026-09-20 — `php -v`,
`composer --version`, `composer show`, `php --ri pcov` — not what a registry page said.

| Thing | Installed | The one install line |
|---|---|---|
| PHP | **8.5.10** (cli, NTS; Debian trixie) | `FROM php:8.5-cli` — the official image; nothing is installed on the host |
| Composer | **2.10.3** (2026-08-27) | `COPY --from=docker.io/library/composer:2 /usr/bin/composer /usr/local/bin/composer` in the `Dockerfile` |
| Slim | **4.15.3**, with `slim/psr7` **1.8.0** | `composer require slim/slim:"4.*" slim/psr7` |
| swagger-php (OpenAPI from attributes) | **6.9.0** | `composer require zircote/swagger-php`; `vendor/bin/openapi src` prints the document |
| PHPUnit | **13.3.4** | `composer require --dev phpunit/phpunit` |
| Infection (mutation testing) | **0.35.4** | `composer require --dev infection/infection` — needs `config.allow-plugins` for `infection/extension-installer` in `composer.json`, or a non-interactive install fails |
| PHPStan (static analysis) | **2.2.14** | `composer require --dev phpstan/phpstan` |
| PCOV (coverage driver) | **1.0.12** | `RUN pecl install pcov-1.0.12 && docker-php-ext-enable pcov` in the `Dockerfile` |

The project's own version lives in `composer.json`'s `version` key. `/orc-version` does not edit
`composer.json` yet — `versionfiles.py`'s `KNOWN_FORMATS` has no entry for it (BACKLOG #6, where
`composer.json` was added on 2026-09-20) — so bump it by hand until it does.

## The stack decision

A PHP back end is one program that a web server hands each request to and that answers with JSON,
or with HTML if the project wants pages. PHP itself is the language and the runtime; the choice is
what receives the request and routes it — a framework — and the framework is judged on three
constraints, in this order (v24 spec §2): it must run on **shared hosting** (Apache or PHP-FPM
pointed at a `public/` directory, no long-running process, no Node build step, no PHP extension
beyond what the official image ships); a **JSON route must be the simplest thing it does**; and
a framework that **produces an OpenAPI description from the code** is ahead of one that does
not, because that document is the contract a consuming app is written against.

**The runtime: PHP 8.5.** php.net's supported-versions table (confirmed live 2026-09-20) lists
8.5 as released 20 Nov 2025 with active support — *"Reported bugs and security issues are fixed
and regular point releases are made"* — until **31 Dec 2027** and security support until 31 Dec
2029; 8.4's active support ends 31 Dec 2026, so 8.5 is the branch with the longest runway a host
can offer today. The official `php` image's current tag list carries `8.5-cli` (8.5.10 today,
Debian trixie), the variant whose README says *"contains the PHP CLI tool with default mods"*;
the `-fpm` and `-apache` variants are for serving, which the development container does not do.

**The framework: Slim 4, with `slim/psr7` and `zircote/swagger-php`.** Slim's own words
(slimframework.com/docs/v4, confirmed live 2026-09-20): *"Slim is a PHP micro framework that
helps you quickly write simple yet powerful web applications and APIs. At its core, Slim is a
dispatcher that receives an HTTP request, invokes an appropriate callback routine, and returns an
HTTP response. That's it."* Against the three constraints:

1. *Shared hosting.* Slim's deployment page has a section headed *"Deploying to a shared
   server"* — *"If your shared server runs Apache, then you need to create a .htaccess file in
   your web server root directory (usually named htdocs, public, public_html or www)"* with a
   rewrite to `public/`, and then *"upload all the files that make up your Slim project to the
   webserver. As you are on shared hosting, this is probably done via FTP"*. Its system
   requirements are *"Web server with URL rewriting"* and *"PHP 7.4 or newer"*; no Node, no
   daemon, no extension. It is the only one of the three candidates whose docs name shared
   hosting at all.
2. *JSON first.* The response page's *"Returning JSON"* is `json_encode`, `write`, and
   `withHeader('Content-Type', 'application/json')` — three lines on a PSR-7 response, nothing
   to configure. A route is `$app->get('/greet', GreetAction::class)`: the routing page says
   *"You could specify a Class which implements the __invoke() method instead of a Closure"*.
3. *OpenAPI from the code.* Slim has no generator of its own; `zircote/swagger-php` (6.9.0,
   2026-09-13; PHP ≥ 8.2) is framework-independent — *"a library that extracts API metadata from
   your PHP source code files … swagger-php will convert those into machine-readable OpenAPI
   documentation"*. Its minimum-requirements page shows a whole valid document from one
   `#[OA\Info(title:, version:)]` and one method carrying `#[OA\Get(path:)]` and
   `#[OA\Response(response:, description:)]`; *"PHP Attributes are the preferred way to annotate
   your code"*, and the attributes go on a class or method (*"associated with structural
   elements (classes, methods, properties, etc.)"*), which is why the route handler is an
   invokable class in `src/` and not a closure in `index.php`. The document is written by
   `./vendor/bin/openapi src -o openapi.yaml` (*"By default, the output format is YAML. If a
   filename is given … the tool will use the file extension to determine the format"*). The cost
   is that every route carries its attributes by hand — the concern that picks the runner-up.

By the selection rule — the easiest option that works — Slim wins: three packages, every
constraint met on a first-party page, and nothing to remove. Versions today (Packagist,
2026-09-20): `slim/slim` **4.15.3** (2026-09-01; requires PHP up to `~8.5.0`), `slim/psr7`
**1.8.0** (2025-11-02) — Slim's installation page: *"you will need to choose a PSR-7
implementation … Slim PSR-7: composer require slim/psr7"* — and `zircote/swagger-php` **6.9.0**.
Install: `composer require slim/slim:"4.*" slim/psr7 zircote/swagger-php`.

**Alternative:** *Laravel 13 with Scramble* — `laravel/framework` **v13.32.0** (2026-09-15; PHP
≥ 8.3), `dedoc/scramble` **v0.13.45** (2026-09-18). Laravel's docs (laravel.com/docs/13.x,
confirmed live 2026-09-20): *"Laravel may also serve as an API backend to a JavaScript
single-page application or mobile application … you may use Laravel to provide authentication
and data storage / retrieval for your application, while also taking advantage of Laravel's
powerful services such as queues, emails, notifications, and more."* Scramble: *"It generates
API documentation for your project automatically without requiring you to manually write PHPDoc
annotations"* — the strongest answer to constraint 3 of any candidate. Concern that picks it: the
API needs what Laravel bundles on day one (accounts, queues, an ORM) or the OpenAPI document
should fall out of the code's own types rather than attributes maintained by hand. What it costs
against constraint 1: its creation command is `laravel new example-app` followed by `npm install
&& npm run build` — *"you should install either Node and NPM or Bun so that you can compile your
application's frontend assets"* — its deployment page names Nginx and FrankenPHP and says
*"long-running services such as queue workers … should be reloaded / restarted"* on deploy, and
it says nothing about shared hosting (searched the deployment page, 2026-09-20: no "shared").

The other two candidates lost on the same page they were read from. *Symfony 8.1 with API
Platform* (`symfony/framework-bundle` v8.1.7, PHP ≥ 8.4; `api-platform/core` v5.0.0, 2026-09-16)
does document a hosting provider that *"requires you to change the public/ directory to another
location (e.g. public_html/)"*, and API Platform's getting-started is `symfony new bookshop-api`,
`symfony composer require api`, then `doctrine:database:create` — an ORM and a resource model
before the first JSON route, which is more than constraint 2 asks for. *Plain PHP, no framework*
passes constraint 1 by definition; php.net's own server is *"designed to aid application
development … It should not be used on a public network"*, so production is Apache either way,
and without a router the `.htaccess`, the request parsing and the JSON headers are written by
hand — the parts Slim's three lines are.

## Build, run, test

Every line below was run on 2026-09-20 inside the container, from the project root, as
`podman compose run --rm -T --workdir "$PWD" orclab <command>` — `podman` is the engine on
this machine; `docker compose run` takes the same words. That prefix is written once here and
implied for the rest of the block.

```bash
composer install                                  # once, and after every composer.json change; writes vendor/ and composer.lock
php -S localhost:8080 -t public                   # dev server: php.net's built-in server, document root public/ (its Example #2 is `-t foo/`)
vendor/bin/phpunit                                # tests: OK (2 tests, 2 assertions)
vendor/bin/phpunit --coverage-clover .orclab/test/php/clover.xml --coverage-html .orclab/test/php/html
vendor/bin/infection --no-interaction --no-progress --threads=max --with-uncovered   # mutation; the JSON log lands where infection.json5's logs.json says
composer audit --format=json --locked             # dependency advisories from Packagist; exit 0 clean, 1 with findings
vendor/bin/phpstan analyse --no-progress --error-format=raw          # static analysis at phpstan.neon's level; a single file: append its path
vendor/bin/openapi src                            # the OpenAPI document from the attributes, YAML to stdout; -o openapi.yaml writes it
```

What each one printed, so the reader knows what right looks like. `composer install` on a
project with no `composer.lock` resolves and writes one first; it ends with
`infection/extension-installer: No extensions found`, which is normal. `phpunit` with the
coverage flags prints `Runtime: PHP 8.5.10 with PCOV 1.0.12` — the same line without `with
PCOV` means the driver is missing and no report will be written. `infection` ends with a
`Metrics:` block (`Mutation Score Indicator (MSI)`, `Mutation Code Coverage`, `Covered Code
MSI`) and exits 0 whatever the score unless `--min-msi` is given; it has **no `--logger-json`
option** (its options page lists `--logger-text`, `--logger-html`, `--logger-summary-json`,
`--logger-github`, `--logger-gitlab`), so the full JSON log is the `logs.json` key in
`infection.json5` — `.orclab/test/php/infection.json` in Orclab's layout. `--with-uncovered` is
there because Infection's default since 0.31 mutates covered code only (*"--only-covered … was
removed in Infection 0.31.0, use --with-uncovered instead"*): without it a class no test reaches
is simply absent from the count, and the sample's untested route handler gave `2 mutants, MSI
100%` — with it, `10 mutants, 8 not covered, MSI 20%`, which is the number that means what
`/orc-test`'s other languages mean by it. `composer audit --format=json` prints one JSON object
to stdout: `advisories` is a dict keyed by package name when there are findings and an empty
list when there are none. `phpstan … --error-format=raw` prints one `path:line:message` per
finding to stdout and exits 1; nothing but a `Note: Using configuration file …` line on stderr
when clean, exit 0. The dev server answered `GET /greet?name=Ada` with `{"greeting":"Hello,
Ada"}` from inside the container — but see `## Containers` for why a browser on the host cannot
reach it.

Three things the run taught about the tests themselves. PHPUnit marks a test with no
assertions *risky* and still exits 0; Infection's own initial run does not — it writes its own
PHPUnit configuration, fails on a risky test, and stops with *"Project tests must be in a
passing state before running Infection"*. So an assertion-free test blocks mutation testing
outright, which makes PHPUnit's risky check the test-smell lint this stack has. Second, PHPUnit
13 runs with PCOV and needs no mode switch or `-d` option; Infection passes `-d
pcov.directory=<src>` itself. Third, `composer.lock` should be committed: `composer audit
--locked` reads it, and `composer install` from it gives every machine the same `vendor/`;
`vendor/`, `.orclab/` and `.phpunit.cache/` are git-ignored.

Coverage, mutation and audit through `/orc-test`: not yet — this section records the commands
that ran; `skills/orc-test/languages/php.md` and the `php.py` language module are v24's next
tasks, and until they land `/orc-test` does not know PHP exists.

## Lint — where code-discipline lands

The sample's `phpstan.neon` (`## Build, run, test` above, confirmed live 2026-09-20):

```neon
parameters:
    level: max
    paths:
        - src
        - public
```

`level: max` is PHPStan's own alias for its highest numbered level — *"You can also use `--level
max` as an alias for the highest level. This will ensure that you will always use the highest
level when upgrading to new versions of PHPStan"* (`phpstan.org/user-guide/rule-levels`,
confirmed live 2026-09-20). PHP has no compiler warnings of its own — like `stack-web`'s Python
half, where *"ruff and pyright are the analyzer… both exit non-zero on a finding, and that is the
warnings-as-errors switch"* — so PHPStan itself is the analyzer, and rule 7's switch is turning
that analyzer all the way up: `level: max`'s ten levels (0–10) accumulate strictness, from level
0's *"always undefined variables"* through level 1's *"possibly undefined variables"*, level 3's
*"return types, types assigned to properties"*, level 6's *"report missing typehints"*, level 8's
*"report calling methods and accessing properties on nullable types"*, level 9's *"be strict
about explicit `mixed` type"*, to level 10's, new in PHPStan 2.0, *"be even more strict about the
`mixed` type — reports errors even for implicit mixed"* (same page) — every one of them a
build-blocking error at `max`, never an advisory. `phpstan/phpstan-strict-rules`
(`github.com/phpstan/phpstan-strict-rules` README, confirmed live 2026-09-20; not in this
project's `composer.json`) turns the same analyzer up further: `checkAlwaysTrueInstanceof`,
`checkAlwaysTrueCheckTypeFunctionCall` and `checkAlwaysTrueStrictComparison` — *"Always true
`instanceof`, type-checking `is_*` functions and strict comparisons `===`/`!==`"* — are more
findings in the same zero-warnings bucket, not a different rule. None of PHPStan's ten levels or
`phpstan-strict-rules`' table mention nesting depth, function length, or an empty `catch` block.

Rule 5 (a check on a caller's, a file's or the network's input, written with `raise`/`require`/
an exception so it survives release) is not what either tool does — PHPStan and
`phpstan-strict-rules` both check that the code is internally type-consistent, at analysis time,
not that a value crossing into the program at runtime gets validated. `stack-web`'s own Lint
section draws the same line for pyright strict, which narrows types the same way PHPStan does and
is still listed under "reviewed, not linted" rather than credited against rule 5. PHP follows the
same call here: rule 5 is reviewed, not linted.

Rules 1 (nesting ≤ 2 levels) and 4 (≈60 lines) need a tool this project does not carry yet: PHP
CodeSniffer's `Generic.Metrics.NestingLevel` (`nestingLevel` warns past its default of 5,
`absoluteNestingLevel` errors past 10) and `Generic.Metrics.CyclomaticComplexity` (`complexity`
warns past 10, `absoluteComplexity` errors past 20) —
`github.com/PHPCSStandards/PHP_CodeSniffer/wiki/Customisable-Sniff-Properties`, confirmed live
2026-09-20. Neither PHPStan nor `phpstan-strict-rules` measures either one. Rules 2 and 3 (a
bounded loop, a resource closed on the error path), rule 5, and rule 6 (never swallow an error)
are all reviewed, not linted — no PHPStan rule level and no `phpstan-strict-rules` entry covers
an empty `catch` either, and adding `phpcs` is future work, not something this stack runs today.

Rule 7's switch also has a PHP-language form, on top of the analyzer above: `declare(strict_types=1);`
at the top of every file. PHP's manual states the default plainly — *"By default, PHP will coerce
values of the wrong type into the expected scalar type declaration if possible"* — against strict
mode: *"In strict mode, only a value corresponding exactly to the type declaration will be
accepted, otherwise a `TypeError` will be thrown"*
(`php.net/manual/en/language.types.declarations.php#language.types.declarations.strict`,
confirmed live 2026-09-20). A coerced value that silently becomes the "wrong but close enough"
type is exactly the kind of defect rule 7 wants surfaced on day one rather than found in week
three; `declare(strict_types=1)` is what turns it into a `TypeError` instead.

`lint_on_write` looks for `phpstan.neon`, then `phpstan.neon.dist`, then `phpstan.dist.neon` —
PHPStan's own lookup order — and when one is found, runs the project's own `vendor/bin/phpstan`
(falling back to `phpstan` on PATH) as `analyse --no-progress --error-format=raw` on every `.php`
file Claude writes, through the container when the project has one.

## Containers

Runs in a container: **yes** — run here 2026-09-20. Every command in `## Build, run, test`
ran inside; what did not is reaching the dev server from a browser on the host.

The `Dockerfile` the run ended with, which `/orc-code` writes when the user says yes to the
container question:

```dockerfile
FROM php:8.5-cli
COPY --from=docker.io/library/composer:2 /usr/bin/composer /usr/local/bin/composer
RUN apt-get update && apt-get install -y unzip
RUN pecl install pcov-1.0.12 && docker-php-ext-enable pcov
```

Line by line, and where each came from. `FROM php:8.5-cli` — the official `php` image's tag
list; its README says the `-cli` variant *"contains the PHP CLI tool with default mods"*, which
is all a development container runs. `COPY --from=docker.io/library/composer:2 …` — the
`composer` image README's own multi-stage line is `COPY --from=composer /usr/bin/composer
/usr/bin/composer`; the registry prefix is this machine's (see the record below), and
`/usr/local/bin` is where the `php` image already puts `php`. `RUN apt-get update && apt-get
install -y unzip` — Composer's introduction page: *"For decompressing files, Composer relies on
tools like 7z (or 7zz), gzip, tar, unrar, unzip and xz"*; the `php` image ships neither `unzip`
nor `7z` nor the `zip` extension, and Packagist's archives are zips, so without this line
`composer install` cannot unpack a single package. `RUN
pecl install pcov-1.0.12 && docker-php-ext-enable pcov` — the `php` README's pattern for a PECL
extension, with the version pinned because the README says *"It is strongly recommended that
users use an explicit version number in their pecl install invocations"*; PCOV because PHPUnit
names *"the PCOV or Xdebug extensions"* and Infection *"Xdebug, phpdbg, or pcov"*, and PCOV
needs no mode switch. Its 1.0.12 release (2024-12-04) predates PHP 8.5 and had never been built
against it by Orclab before today; it compiled cleanly in the image (`PCOV version => 1.0.12`
from `php --ri pcov`), so the Xdebug fallback was not needed.

The `compose.yaml` is the one in `skills/orc-test/SKILL.md`'s Containers section, unchanged.
The project's dependencies live in `vendor/` inside the mounted tree, not in the image, so
`composer install` is run through the container once, and again after every `composer.json`
change; a new tool version is a `composer update` in the same place. Only the two things the
`Dockerfile` names — Composer itself and the coverage extension — need `<engine> compose build
orclab` to change. What cannot happen inside: reaching `php -S localhost:8080` from a browser —
the compose file publishes no port, so the dev loop is either the host's PHP or a `ports:` line
the first project adds and records. The container is a development environment, not what
ships; `## Deployment` is the shared host's own PHP.

The proposal `/orc-code` makes for this stack's container question: **yes** — PHP is the
toolchain unusual on a dev machine, and this machine's apt has 8.3 where the host runs 8.5:
Ubuntu 24.04's own `php` package is 8.3 (`apt-cache madison php`, 2026-09-20), and the 8.5.10
on this host came from a third-party PPA (Ondřej Surý's) that had to be added first. A machine
without that PPA has a PHP two branches behind the image's, and the tests' coverage driver and
the mutation runner are a PECL build on top of that.

**The record of the run, 2026-09-20.** Build: the first `podman compose build orclab` pulled
`php:8.5-cli` (580 MB) and `composer:2` (228 MB) and took about 5 s of pull plus 5–10 s of
build per attempt; the final image `localhost/v24check_orclab` is **607 MB**. Three fixes were
needed before every tool ran, each a finding:

1. **`COPY --from=composer:2` failed on Podman 4.9.3** with *"no stage or image found with that
   name"*. `FROM php:8.5-cli` had resolved because `/etc/containers/registries.conf.d/shortnames.conf`
   aliases `php` to `docker.io/library/php`; there is no `composer` alias and no
   `unqualified-search-registries` on this machine, so a bare name in `COPY --from` has nowhere
   to go (the `composer` README's bare `COPY --from=composer` assumes an engine that fills in
   Docker Hub). The fix is the fully-qualified name, which needs no alias on either engine.
2. **`composer install` failed with** *"The zip extension and unzip/7z commands are both
   missing"* — the `php:8.5-cli` image has neither. The `docker-php-ext-install zip` route
   (with `libzip-dev`) also worked, but Composer then warned *"As there is no 'unzip' nor '7z'
   command installed zip files are being unpacked using the PHP zip extension … any UNIX
   permissions (e.g. executable) defined in the archives will be lost"*, so the line is
   `unzip`, the tool Composer's own page names, and the warning is gone.
3. **`podman compose build` exits 0 when the build fails** — the first attempt printed `exit
   code: 125` and the shell saw 0, exactly the podman-compose 1.0.6 quirk `skills/orc-test/SKILL.md`
   records. Read the build output for `COMMIT` and `Successfully tagged`; do not trust the exit
   code.

Not fixes but findings, recorded once here and in the fixture READMEs: Infection refuses a
risky test and has no `--logger-json`; its default omits uncovered code (`--with-uncovered`
above); `composer audit`'s `advisories` changes type between clean and not; and Composer 2.10
**refuses to lock a version with a published advisory** (`policy.advisories.block` defaults to
true — *"any package versions affected by security advisories will be blocked and cannot be used
during a composer update/require/delete commands"*), so the vulnerable fixture needed
`composer update --no-blocking` to exist at all. Clover's `file name=` and Infection's
`originalFilePath` are absolute container paths, which under Orclab's `compose.yaml` are the
same paths on the host.

## Sources (live on 2026-09-20)

- Runtime: `https://www.php.net/supported-versions.php` (8.5's row: 20 Nov 2025, active until 31 Dec 2027, security until 31 Dec 2029; the "active support" definition); `https://raw.githubusercontent.com/docker-library/docs/master/php/README.md` (the `8.5-cli` tag list at 8.5.10-trixie, the CLI/FPM/Apache variant descriptions, `pecl install` + `docker-php-ext-enable`, *"It is strongly recommended that users use an explicit version number in their `pecl install` invocations"*); `https://raw.githubusercontent.com/docker-library/docs/master/composer/README.md` (`COPY --from=composer /usr/bin/composer /usr/bin/composer` under "multi-stage builds"); `https://raw.githubusercontent.com/docker-library/official-images/master/library/composer` (tags `2.10.3, 2.10, 2, latest`); `https://pecl.php.net/rest/r/pcov/allreleases.xml` and `.../1.0.12.xml` (PCOV 1.0.12 stable, 2024-12-04); `https://raw.githubusercontent.com/krakjoe/pcov/develop/README.md` (`pcov.enabled`, `pcov.directory` defaults); `https://launchpad.net/~ondrej/+archive/ubuntu/php/+sourcepub/17837310/+listing-archive-extra` (pcov 1.0.12 built as `php8.5-pcov`, the evidence it compiles on 8.5 before Task 2's build proves it)
- Coverage driver: `https://docs.phpunit.de/en/13.0/code-coverage.html` (*"leverages the code coverage functionality provided by the PCOV or Xdebug extensions"*); `https://infection.github.io/guide/installation.html` (*"Infection requires a recent version of PHP, and Xdebug, phpdbg, or pcov enabled"*; PHP 8.3.0 needs Infection ≥ 0.32.7); `https://infection.github.io/guide/usage.html` (`source.directories`, `logs.json`, `mutators.@default`, `initialTestsPhpOptions`; the Xdebug/phpdbg/`--coverage` run modes)
- Framework, chosen: `https://www.slimframework.com/docs/v4/` (the micro-framework paragraph, "How does it work?"), `/docs/v4/start/installation.html` (requirements; `composer require slim/slim:"4.*"`; the PSR-7 list with `slim/psr7`), `/docs/v4/start/web-servers.html` (`php -S`, Apache `.htaccess`, Nginx `root /path/to/public`), `/docs/v4/deployment/deployment.html` ("Deploying to a shared server", `displayErrorDetails` false), `/docs/v4/objects/response.html` ("Returning JSON"), `/docs/v4/objects/routing.html` (invokable class routes, `::class`), `/docs/v4/objects/request.html` (`getQueryParams()`); `https://zircote.github.io/swagger-php/guide/` (what it is), `/guide/installation.html` (`composer require zircote/swagger-php`), `/guide/using-attributes.html` (attributes preferred; nesting), `/guide/minimum-requirements.html` (the one-`Info`-one-`Get` minimal document and where attributes may go), `/guide/generating-openapi-documents.html` (`./vendor/bin/openapi app -o openapi.yaml`, `--format`, the `Builder` API)
- Framework, alternatives: `https://laravel.com/docs/13.x/installation` ("Laravel the API Backend"; the Node/NPM sentence; `laravel new` + `npm install && npm run build`; `composer global require laravel/installer`), `https://laravel.com/docs/13.x/deployment` (PHP ≥ 8.3 and the extension list; Nginx; FrankenPHP; `php artisan reload`; no "shared"); `https://scramble.dedoc.co/` (the "without … annotations" sentence; OpenAPI 3.1.0); `https://symfony.com/doc/current/setup.html` (PHP 8.4 or higher; `symfony new … --version="8.1.*"`; `composer create-project symfony/skeleton:"8.1.*"`), `https://symfony.com/doc/current/setup/web_server_configuration.html` (`public/` as document root; the `public_html/` sentence; `symfony/apache-pack`); `https://api-platform.com/docs/symfony/` (`symfony composer require api`, `doctrine:database:create`); `https://www.php.net/manual/en/features.commandline.webserver.php` (the built-in server's warning)
- Tool set: `https://docs.phpunit.de/en/13.0/installation.html` (*"PHPUnit 13 requires PHP 8.4"*; `composer require --dev phpunit/phpunit`), `/en/13.0/cli-options.html` (`--coverage-clover <file>`, `--coverage-text`, `--coverage-xml`, `--fail-on-risky`), `/en/13.0/configuration.html` (`bootstrap`, `cacheDirectory`, `<source><include><directory suffix=".php">src</directory>`), `/en/13.0/risky-tests.html` (*"By default, PHPUnit is strict about tests that do not test anything: tests that do not perform assertions"*); `https://infection.github.io/guide/command-line-options.html` (`--logger-text`, `--logger-html`, `--logger-summary-json`, `--logger-github`, `--logger-gitlab`, `--min-msi`, `--coverage`, `--no-progress`, `--static-analysis-tool`; no `--logger-json` — the full JSON log is the `logs.json` config key); `https://phpstan.org/user-guide/getting-started` (`composer require --dev phpstan/phpstan`; `vendor/bin/phpstan analyse src tests`), `https://phpstan.org/user-guide/command-line-usage` (`--level`, `--configuration`, `--error-format`, exit code 0 means no errors), `https://phpstan.org/user-guide/output-format` (`table`, `raw`, `checkstyle`, `json`, `prettyJson`, `junit`, `github`, …), `https://phpstan.org/user-guide/rule-levels` (`--level max` as the alias for the highest level; level 10 is the top today), `https://phpstan.org/config-reference` (`phpstan.neon` lookup order; `parameters: level:` and `paths:`); `https://getcomposer.org/doc/03-cli.md` (`audit`: exit `0` no issues, `1` findings or missing packages; `--format` table/plain/json/summary; `--locked`; `--abandoned`; `--no-dev`), `https://getcomposer.org/doc/06-config.md` (`allow-plugins`: *"Defaults to {} which does not allow any plugins to be loaded"*, and the interactive prompt); `https://raw.githubusercontent.com/phpstan/phpstan-phpunit/2.0.x/README.md` and `https://raw.githubusercontent.com/phpstan/phpstan-strict-rules/2.0.x/README.md` (neither has an assertion-free-test rule; PHPUnit's own risky-test check is that rule); Packagist searches `https://packagist.org/search.json?q=phpunit%20assertion%20rule` and `?q=test%20without%20assertion` (nothing relevant)
- The live run (2026-09-20, `## Build, run, test` and `## Containers`): `https://raw.githubusercontent.com/docker-library/docs/master/php/README.md` again, its "PHP Core Extensions" example (`apt-get install -y … && docker-php-ext-install -j$(nproc) gd`) and "How to install more PHP extensions"; `https://raw.githubusercontent.com/docker-library/docs/master/composer/README.md` (the bare `COPY --from=composer` line under multi-stage builds); `https://getcomposer.org/doc/00-intro.md` (*"For decompressing files, Composer relies on tools like 7z (or 7zz), gzip, tar, unrar, unzip and xz"*); `https://getcomposer.org/doc/03-cli.md` (`audit`: `0 No issues; 1 Found packages matching dependency policies or failed due to missing required packages`; `--locked`: *"Audit packages from the lock file, regardless of what is currently in vendor dir"*; `--no-blocking`: *"Disables all policy based dependency blocking during this command"*; `--no-security-blocking` deprecated for it); `https://getcomposer.org/doc/06-config.md` (`policy.advisories.block`, the successor of `audit.block-insecure`: *"Defaults to true. If true, any package versions affected by security advisories will be blocked and cannot be used during a composer update/require/delete commands, unless the security advisories are ignored"*); `https://infection.github.io/guide/command-line-options.html` again (`--with-uncovered`: *"Allow mutation of code not covered by tests"*; `--only-covered`: *"This option was removed in Infection 0.31.0, use --with-uncovered instead"*); `https://www.php.net/manual/en/features.commandline.webserver.php` again (`-t` for the document root; Example #2 `php -S localhost:8000 -t foo/`); `https://packagist.org/api/security-advisories/?packages[]=guzzlehttp/guzzle` (fifteen advisories, fourteen covering 7.4.0); this machine's `/etc/containers/registries.conf.d/shortnames.conf` and `registries.conf` (a `php` alias, no `composer` alias, no `unqualified-search-registries`) and `apt-cache madison php` (noble's own 2:8.3, the PPA's 2:8.4, `php8.5-cli` 8.5.10 installed from the PPA)
- Versions: `https://repo.packagist.org/p2/<vendor>/<name>.json` and `https://packagist.org/packages/<vendor>/<name>.json` for `phpunit/phpunit` 13.3.4 (2026-09-15, PHP ≥ 8.4.1), `infection/infection` 0.35.4 (2026-09-02, PHP ^8.3; requires the `infection/extension-installer` Composer plugin), `phpstan/phpstan` 2.2.14 (2026-09-12), `slim/slim` 4.15.3, `slim/psr7` 1.8.0, `zircote/swagger-php` 6.9.0, `laravel/framework` v13.32.0, `laravel/laravel` v13.10.1, `dedoc/scramble` v0.13.45, `symfony/framework-bundle` v8.1.7 (2026-09-14, PHP ≥ 8.4.1), `api-platform/core` v5.0.0, `phpstan/phpstan-strict-rules` 2.0.12, `phpstan/phpstan-phpunit` 2.0.18, `composer/composer` 2.10.3 (2026-08-27)
- Lint (Task 4, `## Lint`): `https://phpstan.org/user-guide/rule-levels` again, this time for each level's own wording (level 0 *"always undefined variables"*, level 1 *"possibly undefined variables"*, level 3 *"return types, types assigned to properties"*, level 6 *"report missing typehints"*, level 8 *"report calling methods and accessing properties on nullable types"*, level 9 *"be strict about explicit `mixed` type"*, level 10 *"be even more strict about the `mixed` type — reports errors even for implicit mixed"*) and the `--level max` alias sentence; `https://github.com/phpstan/phpstan-strict-rules` README's rule table (`checkAlwaysTrueInstanceof`, `checkAlwaysTrueCheckTypeFunctionCall`, `checkAlwaysTrueStrictComparison`, and the rest — no empty-`catch` or nesting/length rule among them); `https://github.com/PHPCSStandards/PHP_CodeSniffer/wiki/Customisable-Sniff-Properties` (`Generic.Metrics.NestingLevel`: `nestingLevel` default 5, `absoluteNestingLevel` default 10; `Generic.Metrics.CyclomaticComplexity`: `complexity` default 10, `absoluteComplexity` default 20); `https://phpstan.org/config-reference` again, its automatic config-file lookup order (`phpstan.neon`, then `phpstan.neon.dist`, then `phpstan.dist.neon`); `https://www.php.net/manual/en/language.types.declarations.php#language.types.declarations.strict` (coercive mode: *"By default, PHP will coerce values of the wrong type into the expected scalar type declaration if possible"*; strict mode: *"In strict mode, only a value corresponding exactly to the type declaration will be accepted, otherwise a `TypeError` will be thrown"*)
