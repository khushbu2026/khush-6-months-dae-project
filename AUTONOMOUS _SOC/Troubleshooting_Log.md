# Autonomous SOC — Setup Troubleshooting Log

**Scope:** Every error hit while wiring Claude Desktop → n8n → Wazuh into a working (semi-)autonomous SOC pipeline, in the order they happened. Each entry gives the literal error, a plain-English explanation, the technical explanation, how it was fixed, and how to recognize/fix it yourself next time.

**Not covered:** anything from earlier semesters' work this session didn't touch — this log only covers what happened in this live-deployment session.

---

## 1. The core constraint — Claude Desktop needs HTTPS, n8n only gives HTTP

n8n's MCP server address is `http://localhost:5678/mcp-server/http`. Claude Desktop's "Add custom connector" screen only accepts `https://` URLs.

**Plain English:** Claude Desktop's *point-and-click* connector form has a rule: the address has to start with the secure `https://`, not the plain `http://`. n8n, running locally, only speaks plain `http://` out of the box. Two systems with a mismatched requirement.

**Technical:** This restriction lives specifically in Claude Desktop's OAuth-capable "remote connector" GUI, which assumes a publicly reachable, TLS-terminated endpoint (because OAuth redirects and dynamic client registration are designed for the public web). It is **not** a restriction on Claude Desktop's underlying MCP client in general — only that specific GUI flow.

**How it was resolved:** Ultimately we bypassed this constraint entirely (see #7) by using Claude Desktop's config-file server format instead of the GUI connector, which talks to `http://localhost` directly with no HTTPS requirement at all. The HTTPS tunnel work (below) turned out to be unnecessary for the final solution — useful to know before spending time on tunnels.

**Self-diagnose next time:** If a GUI only accepts `https://` for something running on your own machine, ask whether there's a config-file / CLI path that doesn't go through that GUI before building tunnel infrastructure.

---

## 2. Homebrew was broken — permissions

```
Error: The following directories are not writable by your user:
  /opt/homebrew /opt/homebrew/Cellar /opt/homebrew/Frameworks ...
```

**Plain English:** The `brew install` command needs to write files into a shared system folder, and your Mac user account wasn't allowed to write there anymore.

**Technical:** Homebrew's `/opt/homebrew` prefix is normally owned by the installing user. At some point ownership had drifted (commonly caused by a prior `sudo brew ...` invocation, or a shared-machine setup) so the directories were no longer writable by the current user. The fix Homebrew itself suggests is `sudo chown -R $(whoami) /opt/homebrew ...`.

**How it was resolved:** We did **not** run the suggested `chown`, since changing system-wide ownership wasn't necessary for the task — Docker was already running, so we ran `cloudflared` and later `ngrok` as Docker containers instead of installing them via Homebrew. Same result, zero permission changes to your system.

**Self-diagnose next time:** If `brew install` fails with a permissions error and you don't want to touch system ownership, check whether the tool you need has an official Docker image first — often faster and it avoids the ownership question entirely.

---

## 3. Containers can't reach "localhost" on the Mac

When running `cloudflared`/`ngrok` in Docker to expose n8n, pointing them at `http://localhost:5678` failed — they had to point at `http://host.docker.internal:5678` instead.

**Plain English:** Inside a Docker container, "localhost" means *the container itself*, not your Mac. Docker containers are like separate little computers — saying "localhost" inside one of them doesn't reach anything running directly on your Mac (or in a sibling container). Docker Desktop provides a special hostname, `host.docker.internal`, that means "the actual Mac (or the container network's gateway) this is running on."

**Technical:** Each container gets its own network namespace. `localhost`/`127.0.0.1` inside a container resolves to that container's own loopback interface. Docker Desktop for Mac injects a DNS entry, `host.docker.internal`, that resolves to the host's (or the bridge network's) address, letting a container reach services published on the host or running in sibling containers via their host-published ports.

**How it was resolved:** Every container that needed to reach n8n (`cloudflared`, `ngrok`) or that n8n needed to reach (Wazuh Indexer, Wazuh Manager API) used `host.docker.internal` instead of `localhost` in its configuration.

**Self-diagnose next time:** Any time one Docker container needs to talk to something exposed on the host or in another container, and `localhost` mysteriously doesn't work (connection refused), try `host.docker.internal` first.

---

## 4. Free tunnel URLs aren't stable

A Cloudflare "quick tunnel" gives a working HTTPS URL immediately, but the subdomain (e.g. `spot-pick-gloves-closes.trycloudflare.com`) is randomly regenerated every time the tunnel restarts — it can't be pinned to a fixed address without a Cloudflare account and a domain you own.

**Plain English:** The free instant tunnel is like a temporary phone number — great for a quick call, useless if you need people to be able to reach the same number tomorrow.

**Technical:** Cloudflare "quick tunnels" (`cloudflared tunnel --url ...` with no named tunnel) are anonymous and ephemeral by design — Cloudflare doesn't let you reserve a fixed hostname without owning a zone (domain) in your Cloudflare account, because the hostname is a DNS record under that zone. A *named* tunnel needs that domain. **ngrok**, by contrast, offers one free *static* domain per account with no domain-ownership requirement — that's why we switched tools mid-task.

**How it was resolved:** Moved from Cloudflare's quick tunnel to ngrok, which let you reserve a permanent free subdomain (`scientist-coeditor-wreath.ngrok-free.dev`) tied to your ngrok account instead of a domain you'd have to own.

**Self-diagnose next time:** If you need a tunnel URL that doesn't change, check whether the tool requires you to own a domain (Cloudflare named tunnels do) before starting — ngrok's free static domain is the lower-friction option when you don't own one.

---

## 5. n8n's OAuth "sign-in service" failed to register Claude Desktop

```
Couldn't register with n8n's sign-in service. You can try again, or add an
OAuth Client ID in the connector settings.
Reference: "ofid_e916c1f7e2f08f19"
```

**Plain English:** n8n offered to let Claude Desktop log in automatically (like clicking "Sign in with Google"), but the handshake that sets that up failed on n8n's side.

**Technical:** n8n's "Instance-level MCP" preview feature can require OAuth 2.1, including **Dynamic Client Registration (RFC 7591)** — where the connecting client (Claude Desktop) automatically registers itself with the server's OAuth authorization endpoint at connection time, with no pre-shared app credentials. This flow is primarily built and tested for n8n's own hosted cloud OAuth service; on a self-hosted instance, that registration step doesn't reliably complete.

**How it was resolved:** Abandoned the OAuth path entirely. Switched n8n's MCP auth to **Access Token** mode (a static bearer token) instead of OAuth, then connected Claude Desktop using that static token via a different mechanism (see #6 and #7) instead of the GUI's OAuth-based flow.

**Self-diagnose next time:** If a self-hosted tool's OAuth "auto sign-in" fails with a registration error, check whether it offers a plain static API token / access-token mode as an alternative — self-hosted OAuth servers are often less reliable for this than a hosted SaaS equivalent.

---

## 6. First fix attempt also failed — unsupported config format

```
Some MCP servers couldn't be loaded.
The following entries in claude_desktop_config.json are not valid MCP
server configurations and were skipped: n8n-mcp
```

**Plain English:** We tried editing Claude Desktop's settings file directly to add the server with the access token, using a newer format. That specific Claude Desktop build didn't recognize that format and silently skipped the entry.

**Technical:** We first wrote the server entry using the schema `{"type": "http", "url": "...", "headers": {...}}`. This is a newer addition to the `claude_desktop_config.json` schema (remote HTTP servers with custom headers) that hasn't rolled out to every Claude Desktop build yet. The older, universally-supported schema is `{"command": "...", "args": [...], "env": {...}}` — a *local process* Claude Desktop spawns and talks to over stdio.

**How it was resolved:** Switched to the older `command`/`args`/`env` format, using a bridge tool (`mcp-remote`, see #7) that runs as a local process and internally makes the HTTP call with the Authorization header, so Claude Desktop never needs to know about `"type": "http"` at all.

**Self-diagnose next time:** If Claude Desktop silently skips an MCP server entry with a "not valid configuration" popup, suspect a schema-version mismatch first — check your Claude Desktop version against the docs, or fall back to the older `command`/`args`/`env` format, which is the most universally supported.

---

## 7. The real fix needed Node.js, and it wasn't installed

```
/bin/bash: node: command not found
/bin/bash: npx: command not found
```

**Plain English:** The bridge tool that finally worked (`mcp-remote`) is a small JavaScript program. Running any JavaScript program from the command line needs Node.js installed first, and this Mac didn't have it yet.

**Technical:** `npx` is Node's package runner — it downloads and runs an npm package (here, `mcp-remote`) on demand without a separate install step, but it ships as part of Node.js itself, so Node has to exist first. `mcp-remote` is a small stdio↔HTTP proxy: Claude Desktop spawns it as a normal local process (satisfying #6's schema requirement), and internally it opens an HTTP connection to the *real* remote MCP server (n8n), attaching whatever headers you give it (here, the `Authorization: Bearer <token>`).

**How it was resolved:** Installed Node via `nvm` (no `sudo`/Homebrew needed) as a first attempt; you separately installed Node system-wide via the official installer (`/usr/local/bin/node`), which is what the final config points at, since it's a more stable path than an nvm version-numbered one. Verified it worked by running `mcp-remote` manually for a few seconds and confirming the log line `Connected to remote server using StreamableHTTPClientTransport` before wiring it into the real config — this caught any auth/URL problems before burning a Claude Desktop restart cycle on them.

**Self-diagnose next time:** `command not found` for `node`/`npx` always means Node.js isn't installed (or isn't on the `PATH` used by whatever's calling it). Check with `which node` — if empty, install Node (official installer, `nvm`, or Homebrew, in order of "least likely to hit a permissions wall").

---

## 8. A silent trap avoided — `mcp-remote`'s header-parsing bug

**Plain English:** There's a known bug where, on some platforms, if you write an auth header value with a space in it (like `Authorization: Bearer abc123`) directly as a command-line argument, the space can get mangled and break the header. We sidestepped it before it ever caused a problem.

**Technical:** Cursor, Codex-CLI, and Claude Desktop (Windows) have a documented bug where spaces inside a spawned process's arguments aren't escaped correctly when the parent invokes `npx`. The documented workaround is to keep the `--header` argument itself space-free (`Authorization:${VAR}` — no space around the colon) and put the actual value, which does contain a space (`Bearer <token>`), into an **environment variable** referenced by `${VAR}`, since environment variables aren't subject to the same argument-mangling.

**How it was resolved:** The config was written this way from the start: `"--header", "Authorization:${N8N_MCP_AUTH}"` with `"env": {"N8N_MCP_AUTH": "Bearer <token>"}`, rather than embedding the full header inline.

**Self-diagnose next time:** If a bearer-token/API-key header mysteriously doesn't authenticate when passed as a CLI argument but works fine when tested with `curl`, suspect argument-space-mangling — move the value into an environment variable instead.

---

## 9. `git add .` in your home directory nearly staged your entire Mac

Running `git status` revealed `/Users/Adult` itself is a git repository. A plain `git add .` there would have staged **everything**: `.bash_history`, `.zsh_history`, `.claude.json` (session/credential data), `.docker/`, `.npm/`, `.nvm/`, all of `Library/`, `Documents/`, `Downloads/` — and, critically, the n8n access token that had just been written into `claude_desktop_config.json` in plaintext.

**Plain English:** Your whole user folder, not just a project folder, turned out to be tracked by git. Typing the everyday shortcut "stage everything" in that location would have swept up shell history and saved secrets right along with any real project files, all headed toward being committed (and possibly pushed somewhere) if you weren't watching.

**Technical:** `git add .` stages every changed/untracked file under the current directory recursively, with no filtering beyond `.gitignore`. Since the repo root was `/Users/Adult` (not a scoped project directory), "current directory" was the entire home folder. `git status --porcelain` was run first specifically to enumerate what would be staged before running any add — this is the general pattern: **always preview scope before a broad `git add`, especially in an unfamiliar or unexpectedly-large repo.**

**How it was resolved:** The command was not run. The full file list was surfaced instead, and the task was paused for you to clarify exactly what should be staged — it turned out you'd moved on to a different task, so nothing was ever staged.

**Self-diagnose next time:** Before any `git add -A` or `git add .`, run `git rev-parse --show-toplevel` to confirm the repo root is what you think it is, and `git status` to see what's actually about to be staged — especially in a directory you didn't set up yourself.

---

## 10. Wrong Wazuh account used — 401 Unauthorized on the Manager API

```
Indexer (port 9200) with admin/SecretPassword → works.
Manager API (port 55000) with admin/SecretPassword →
{"title":"Unauthorized","detail":"Invalid credentials"}
```

**Plain English:** Wazuh isn't one login for everything — the dashboard/search side and the "management" side use two completely separate accounts, and we initially assumed they were the same.

**Technical:** A Wazuh deployment has (at least) two distinct authentication surfaces: the **Wazuh Indexer** (an OpenSearch fork — the search/storage layer, port 9200, secured by OpenSearch Security with its own `admin` user) and the **Wazuh Manager REST API** (the management/control layer, port 55000, secured by its own RBAC system with a separate service account — commonly `wazuh-wui`, with a separately auto-generated password). They look similar (both HTTP Basic Auth) but are unrelated credential stores. The correct `wazuh-wui` password was found by reading the Wazuh Manager container's environment variables (`API_USERNAME`, `API_PASSWORD`), where it's set at deploy time.

**How it was resolved:** Located the actual `API_USERNAME=wazuh-wui` / `API_PASSWORD=...` pair from the manager container's environment, and confirmed it worked with a direct `curl -X POST https://localhost:55000/security/user/authenticate` test before wiring it into n8n as a separate credential from the Indexer's.

**Self-diagnose next time:** If Wazuh Indexer (9200) accepts your admin login but the Manager API (55000) rejects the same login with `Invalid credentials`, don't assume it's the same account — check the manager container's env (`API_USERNAME`/`API_PASSWORD`) or your deployment's `.env`/docker-compose file for a separate API service account.

---

## 11. n8n credential import failed on a missing ID field

```
SQLITE_CONSTRAINT: NOT NULL constraint failed: credentials_entity.id
```

**Plain English:** We tried to create a login/credential entry in n8n by feeding it a file directly (instead of typing it into the web form), and n8n's database rejected it because we hadn't given it a required internal ID.

**Technical:** n8n's `n8n import:credentials` CLI command writes rows directly into its database (SQLite here). When you create a credential through the web UI, n8n auto-generates a unique `id` for you; the CLI importer does **not** do this — it expects the JSON you feed it to already include an `id` field, and SQLite's `NOT NULL` constraint on that column rejects the insert otherwise.

**How it was resolved:** Generated random 16-character alphanumeric IDs (matching the style n8n itself uses) and included them explicitly in the credential JSON before importing — the second attempt succeeded.

**Self-diagnose next time:** Any time a CLI import tool errors with a `NOT NULL constraint failed` on an `id` column, the fix is almost always "include an explicit unique ID in the record you're importing" — the CLI path skips whatever auto-generation the GUI does for you.

---

## 12. n8n's own CLI test-runner conflicted with the running n8n server

```
n8n Task Broker's port 5679 is already in use.
Do you have another instance of n8n running already?
```

**Plain English:** We tried to test-run a workflow from the command line, inside the same container where n8n was already running as a live server — and the test command tried to start its own internal helper process on a port the live server was already using.

**Technical:** `n8n execute --id=...` spins up n8n's **Task Broker** (an internal component used for scaling task execution) on a fixed local port (5679) as part of a one-off CLI run. Since the container's main `n8n start` process was already running and already holding that port, the second process couldn't bind it and failed immediately.

**How it was resolved:** Abandoned CLI-based execution for this container and tested the workflow through the n8n web UI instead — which is why a temporary manual-trigger test branch (feeding a fake, harmless IP and a non-existent agent ID) was added directly to the workflow, so it could be safely tested by clicking "Execute" in the browser rather than via the CLI.

**Self-diagnose next time:** `n8n execute` (the CLI test-runner) and a running `n8n start` server can't share one container/host — if you need to test a workflow ad hoc, either use the web UI's Execute button, or run the CLI command in a completely separate n8n instance/container that isn't also running the server.

---

## Glossary

| Term | Plain English | Technical |
|---|---|---|
| **MCP** | The "language" Claude uses to call out to external tools (like n8n's workflows). | Model Context Protocol — a standard for exposing tools/resources to an LLM client over stdio or HTTP. |
| **stdio vs. HTTP transport** | stdio = a program running right next to Claude that it talks to directly; HTTP = a separate server somewhere else that Claude talks to over the network. | stdio: parent spawns a child process, communicates over its stdin/stdout. HTTP: client makes network requests to a server URL. `mcp-remote` bridges the two. |
| **`host.docker.internal`** | The special address a Docker container uses to mean "the Mac it's running on" (since "localhost" inside a container means the container itself). | A DNS name Docker Desktop resolves to the host's (or bridge gateway's) address, for container→host/sibling-container traffic. |
| **OAuth 2.1 / Dynamic Client Registration** | "Sign in automatically" — but for two computer programs to be able to do that safely, one first has to formally register itself with the other. | RFC 7591: a client registers itself with an authorization server at connection time (no pre-shared app ID), instead of a developer manually registering an OAuth app in advance. |
| **Bearer token** | A password-like secret string you attach to a request to prove who you are — like a wristband at an event. | A credential sent in the `Authorization: Bearer <token>` HTTP header; the server trusts whoever holds a valid token. |
| **Wazuh Indexer vs. Manager API** | Two different "departments" inside Wazuh with separate logins — one stores/searches alert data, the other lets you control the system (including taking action). | Indexer (port 9200): OpenSearch-based storage/search layer. Manager API (port 55000): RBAC-secured REST control-plane, used here to trigger Active Response. |
| **Active Response** | Wazuh's own built-in "take action automatically" feature — e.g. blocking an IP at the firewall on the affected machine. | A Wazuh Manager API call (`PUT /active-response`) that instructs a specific registered *agent* to run a predefined response script (here, `firewall-drop0`) against a target. |
| **n8n Data Table** | A small built-in spreadsheet-like table inside n8n workflows use to remember state (e.g. "which IPs have already been blocked"). | A first-class n8n entity queried/written by the `n8n-nodes-base.dataTable` node; not manageable via the CLI used in this session. |

---

## Known gaps (not errors — deliberately left unfinished)

- **Grafana annotation step** — needs a Grafana API key (header auth credential); not configured, since no Grafana login was provided.
- **Email notification step** — needs SMTP credentials; not configured, since none were provided. The workflow runs fine up to this point regardless.
- **`blocked_ip_log` Data Table** — existence unverified; n8n's CLI doesn't expose Data Tables, and checking requires logging into the n8n web UI.
- **Auto-Block workflow is inactive on purpose** — the 5-minute schedule trigger has not been turned on. It will not run automatically until you activate it in the n8n UI.
