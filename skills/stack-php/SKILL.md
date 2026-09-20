---
name: stack-php
description: Background knowledge for any work in a PHP web back end - an API alone, behind a React front end from stack-web, or serving HTML itself; creating one, running its tests, coverage and mutation testing, auditing its dependencies, containerising its toolchain, or preparing it for a host that serves PHP and nothing else. Says what the current toolchain is, where things live in the project, and what is not yet known about shared-hosting deployment. Not a command; Claude reads it when PHP is in play.
user-invocable: false
---

# PHP — a web back end

No project has been built with this yet; the first one corrects it. Unlike the other stack
skills, every command below was run in a container on the machine that wrote it (2026-09-DD),
so "not run here" appears only in `## Deployment`.

**Checked against live sources on 2026-09-20**; anything older than one release is suspect — re-check `## Sources`.

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

## Sources (live on 2026-09-20)

- Runtime: `https://www.php.net/supported-versions.php` (8.5's row: 20 Nov 2025, active until 31 Dec 2027, security until 31 Dec 2029; the "active support" definition); `https://raw.githubusercontent.com/docker-library/docs/master/php/README.md` (the `8.5-cli` tag list at 8.5.10-trixie, the CLI/FPM/Apache variant descriptions, `pecl install` + `docker-php-ext-enable`, *"It is strongly recommended that users use an explicit version number in their `pecl install` invocations"*); `https://raw.githubusercontent.com/docker-library/docs/master/composer/README.md` (`COPY --from=composer /usr/bin/composer /usr/bin/composer` under "multi-stage builds"); `https://raw.githubusercontent.com/docker-library/official-images/master/library/composer` (tags `2.10.3, 2.10, 2, latest`); `https://pecl.php.net/rest/r/pcov/allreleases.xml` and `.../1.0.12.xml` (PCOV 1.0.12 stable, 2024-12-04); `https://raw.githubusercontent.com/krakjoe/pcov/develop/README.md` (`pcov.enabled`, `pcov.directory` defaults); `https://launchpad.net/~ondrej/+archive/ubuntu/php/+sourcepub/17837310/+listing-archive-extra` (pcov 1.0.12 built as `php8.5-pcov`, the evidence it compiles on 8.5 before Task 2's build proves it)
- Coverage driver: `https://docs.phpunit.de/en/13.0/code-coverage.html` (*"leverages the code coverage functionality provided by the PCOV or Xdebug extensions"*); `https://infection.github.io/guide/installation.html` (*"Infection requires a recent version of PHP, and Xdebug, phpdbg, or pcov enabled"*; PHP 8.3.0 needs Infection ≥ 0.32.7); `https://infection.github.io/guide/usage.html` (`source.directories`, `logs.json`, `mutators.@default`, `initialTestsPhpOptions`; the Xdebug/phpdbg/`--coverage` run modes)
- Framework, chosen: `https://www.slimframework.com/docs/v4/` (the micro-framework paragraph, "How does it work?"), `/docs/v4/start/installation.html` (requirements; `composer require slim/slim:"4.*"`; the PSR-7 list with `slim/psr7`), `/docs/v4/start/web-servers.html` (`php -S`, Apache `.htaccess`, Nginx `root /path/to/public`), `/docs/v4/deployment/deployment.html` ("Deploying to a shared server", `displayErrorDetails` false), `/docs/v4/objects/response.html` ("Returning JSON"), `/docs/v4/objects/routing.html` (invokable class routes, `::class`), `/docs/v4/objects/request.html` (`getQueryParams()`); `https://zircote.github.io/swagger-php/guide/` (what it is), `/guide/installation.html` (`composer require zircote/swagger-php`), `/guide/using-attributes.html` (attributes preferred; nesting), `/guide/minimum-requirements.html` (the one-`Info`-one-`Get` minimal document and where attributes may go), `/guide/generating-openapi-documents.html` (`./vendor/bin/openapi app -o openapi.yaml`, `--format`, the `Builder` API)
- Framework, alternatives: `https://laravel.com/docs/13.x/installation` ("Laravel the API Backend"; the Node/NPM sentence; `laravel new` + `npm install && npm run build`; `composer global require laravel/installer`), `https://laravel.com/docs/13.x/deployment` (PHP ≥ 8.3 and the extension list; Nginx; FrankenPHP; `php artisan reload`; no "shared"); `https://scramble.dedoc.co/` (the "without … annotations" sentence; OpenAPI 3.1.0); `https://symfony.com/doc/current/setup.html` (PHP 8.4 or higher; `symfony new … --version="8.1.*"`; `composer create-project symfony/skeleton:"8.1.*"`), `https://symfony.com/doc/current/setup/web_server_configuration.html` (`public/` as document root; the `public_html/` sentence; `symfony/apache-pack`); `https://api-platform.com/docs/symfony/` (`symfony composer require api`, `doctrine:database:create`); `https://www.php.net/manual/en/features.commandline.webserver.php` (the built-in server's warning)
- Tool set: `https://docs.phpunit.de/en/13.0/installation.html` (*"PHPUnit 13 requires PHP 8.4"*; `composer require --dev phpunit/phpunit`), `/en/13.0/cli-options.html` (`--coverage-clover <file>`, `--coverage-text`, `--coverage-xml`, `--fail-on-risky`), `/en/13.0/configuration.html` (`bootstrap`, `cacheDirectory`, `<source><include><directory suffix=".php">src</directory>`), `/en/13.0/risky-tests.html` (*"By default, PHPUnit is strict about tests that do not test anything: tests that do not perform assertions"*); `https://infection.github.io/guide/command-line-options.html` (`--logger-text`, `--logger-html`, `--logger-summary-json`, `--logger-github`, `--logger-gitlab`, `--min-msi`, `--coverage`, `--no-progress`, `--static-analysis-tool`; no `--logger-json` — the full JSON log is the `logs.json` config key); `https://phpstan.org/user-guide/getting-started` (`composer require --dev phpstan/phpstan`; `vendor/bin/phpstan analyse src tests`), `https://phpstan.org/user-guide/command-line-usage` (`--level`, `--configuration`, `--error-format`, exit code 0 means no errors), `https://phpstan.org/user-guide/output-format` (`table`, `raw`, `checkstyle`, `json`, `prettyJson`, `junit`, `github`, …), `https://phpstan.org/user-guide/rule-levels` (`--level max` as the alias for the highest level; level 10 is the top today), `https://phpstan.org/config-reference` (`phpstan.neon` lookup order; `parameters: level:` and `paths:`); `https://getcomposer.org/doc/03-cli.md` (`audit`: exit `0` no issues, `1` findings or missing packages; `--format` table/plain/json/summary; `--locked`; `--abandoned`; `--no-dev`), `https://getcomposer.org/doc/06-config.md` (`allow-plugins`: *"Defaults to {} which does not allow any plugins to be loaded"*, and the interactive prompt); `https://raw.githubusercontent.com/phpstan/phpstan-phpunit/2.0.x/README.md` and `https://raw.githubusercontent.com/phpstan/phpstan-strict-rules/2.0.x/README.md` (neither has an assertion-free-test rule; PHPUnit's own risky-test check is that rule); Packagist searches `https://packagist.org/search.json?q=phpunit%20assertion%20rule` and `?q=test%20without%20assertion` (nothing relevant)
- Versions: `https://repo.packagist.org/p2/<vendor>/<name>.json` and `https://packagist.org/packages/<vendor>/<name>.json` for `phpunit/phpunit` 13.3.4 (2026-09-15, PHP ≥ 8.4.1), `infection/infection` 0.35.4 (2026-09-02, PHP ^8.3; requires the `infection/extension-installer` Composer plugin), `phpstan/phpstan` 2.2.14 (2026-09-12), `slim/slim` 4.15.3, `slim/psr7` 1.8.0, `zircote/swagger-php` 6.9.0, `laravel/framework` v13.32.0, `laravel/laravel` v13.10.1, `dedoc/scramble` v0.13.45, `symfony/framework-bundle` v8.1.7 (2026-09-14, PHP ≥ 8.4.1), `api-platform/core` v5.0.0, `phpstan/phpstan-strict-rules` 2.0.12, `phpstan/phpstan-phpunit` 2.0.18, `composer/composer` 2.10.3 (2026-08-27)
