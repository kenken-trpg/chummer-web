# Deploy

One container. Caddy fronts the FastAPI backend and the Next.js standalone
server, supervised by `supervisord`.

```
                       ┌──────────── container ────────────┐
  client ──TLS(edge)──▶ :$PORT  caddy ─┬─ /api/* ─▶ :8000  uvicorn (rules engine)
                       │                └─ /*     ─▶ :3000  next  (standalone)
                       └───────────────────────────────────┘
```

The backend is stateless (see `docs/plans/stateless-refactor.md`); characters live in
the browser. Nothing to back up, safe to scale to zero / run many instances.

## Build & run locally

```bash
docker compose up -d           # http://localhost:8080 (builds from this checkout)
# or
docker build -t chummer-web .
# nothing in the image is written to at run time, so run it locked down —
# `compose.yaml` does the same, and CI smoke-tests this exact shape
docker run --rm -p 8080:8080 \
  --read-only --security-opt no-new-privileges:true --cap-drop ALL \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --tmpfs /app/frontend/.next/cache:rw,noexec,nosuid,size=16m \
  chummer-web
```

`compose.yaml` sets `pull_policy: build`, so the image is rebuilt from the
checkout on every `up`. Cached, that costs seconds, and it is what keeps the
image in step with the file starting it: the read-only / `--cap-drop ALL`
runtime needs the Dockerfile's `setcap -r` on the caddy binary, and an image
predating that fails to exec caddy (`EPERM`) under the compose file that asks
for it. Reusing whatever image the host happens to have turns that into a
container that never becomes healthy.

CI builds the same image for `linux/amd64` and `linux/arm64`, each on its own
native runner, smoke-tests both locked down, and only then joins the two
digests into one tag — so a pull gets the right architecture and never gets an
image that failed to start. It publishes to `ghcr.io/<owner>/chummer-web`, but
a GHCR package is private when first created whatever the repository's
visibility: `docker compose pull` fails with `unauthorized` until someone flips
it once in the package settings. Building is the path that always works; pull
explicitly when you have access and want to skip the build.

### Checking what you pulled

Every published tag is signed, and carries an SBOM of what is actually in its
layers. Both claims are attached to the manifest list — the digest a `docker
pull` resolves — so one check covers both architectures.

```sh
owner=<owner>   # the GitHub account or org the image was published from

# who built it: the signature names the workflow, ref and commit
cosign verify ghcr.io/$owner/chummer-web:latest \
  --certificate-identity-regexp "^https://github.com/$owner/chummer-web/" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

# what is in it
cosign download attestation ghcr.io/$owner/chummer-web:latest \
  | jq -r '.payload | @base64d | fromjson | .predicate' > sbom.spdx.json
grype sbom:sbom.spdx.json      # or any SPDX reader
```

Signing is keyless: there is no public key to distribute, and nothing to rotate.
The certificate is issued to the workflow itself, which is why the identity to
check is a URL rather than a fingerprint — `--certificate-identity-regexp`
above accepts any workflow in that repository, so narrow it to
`.../ci.yml@refs/heads/main` if you want to pin the ref as well. The same SBOM
is on the workflow run as an artifact, for comparing two releases without
cosign.

The Chummer game data is fetched at **build time** (`fetch_chummer_data.py`,
pinned to `CHUMMER_REF`) and baked into the image — no network needed at
runtime. Move the pin with `--build-arg CHUMMER_REF=<sha>`.

## Runtime env

| var | default | note |
| --- | --- | --- |
| `PORT` | `8080` | port Caddy listens on |
| `ALLOWED_ORIGINS` | `localhost:3000` list | only matters for a split deploy (frontend on another origin) |
| `RATE_LIMIT` | `120/minute` | per client IP, all routes |
| `IMPORT_RATE_LIMIT` | `20/minute` | per client IP, the XML-handling routes (imports, settings / customdata upload, .chum5 export and its check) |
| `CSP_REPORT_RATE_LIMIT` | `60/minute` | per client IP, `/api/csp-report` |
| `MAX_REQUEST_BYTES` | `12582912` | 413 above this, chunked bodies included; the bundled Caddy enforces it too |
| `CHUM5_MAX_DECOMPRESSED_BYTES` | `33554432` | `.chum5lz` decompression-bomb cap |
| `TRUSTED_PROXY_HOPS` | `0` | entries in from the right of `x-forwarded-for` that hold the real client |
| `TRUST_CLOUDFLARE_IP` | unset | `1` behind Cloudflare, which sets `cf-connecting-ip`; ignored otherwise |
| `LOG_FORMAT` | `text` | `json` for one object per line |
| `LOG_LEVEL` | `INFO` | root level |

**Logs.** Every response carries `X-Request-ID`, and every log line carries the
same id, so a user quoting the header from their network tab is enough to find
the request. With `TRUSTED_PROXY_HOPS` above 0 an `X-Request-ID` from the edge
is adopted instead, so one id spans the whole hop chain (at 0 the header is
attacker-controlled and is ignored, same rule as the forwarded IP below). The
access line is written by the app, not uvicorn — `uvicorn.access` is quieted to
avoid a second, less useful copy.

`LOG_FORMAT=json` gives one object per line:

```json
{"ts":"…","level":"INFO","logger":"chummer_web","message":"POST /api/characters/patch -> 200 in 41.2ms",
 "request_id":"9f0c1d2e3a4b","method":"POST","path":"/api/characters/patch","status":200,
 "duration_ms":41.2,"client":"203.0.113.7"}
```

Request bodies, query strings and anything derived from a `CharacterState` are
never logged. Characters are the user's and never touch disk on the server; a
log line is disk.

**CSP violations.** The page's Content-Security-Policy names
`/api/csp-report`, and a violation arrives there as one `info` line:

```json
{"level":"INFO","message":"csp violation: script-src-elem blocked https://evil.test/x.js",
 "csp_report":{"document-uri":"https://…/chargen","effective-directive":"script-src-elem",
 "blocked-uri":"https://evil.test/x.js","disposition":"enforce"},"client":"203.0.113.7"}
```

`info` rather than `warning` on purpose: browser extensions and injected page
scripts produce a steady trickle on any public deployment, so the interesting
signal is a *change* in what is reported, not the presence of reports. Only the
fields above are kept, each truncated, and the endpoint answers 204 to anything
— it is the one route whose body is written by something other than our own
client. Turn it down with `CSP_REPORT_RATE_LIMIT`.

**Client IP for rate limiting.** No forwarded header is trusted by default — a
client talking straight to the app can forge one and take one request per fake
IP, straight past every limit. Say what sits in front:

- **Cloudflare (Tunnel or proxied DNS)** — `TRUST_CLOUDFLARE_IP=1`, which reads
  `cf-connecting-ip`; Cloudflare overwrites it on the way in. Without the flag
  the header is ignored, because anywhere else the caller writes it.
- **Cloud Run / Fly.io** — `2` (the platform appends `client, lb-ip`).
- **One self-managed nginx/Caddy** that appends the connecting peer — `1`.

Sanity-check after deploy: hit it from a known IP and confirm that IP (not the
LB's) shows up in a 429 / log line.

Health check: `GET /api/health` (also the image `HEALTHCHECK`) — liveness, 200
as soon as uvicorn binds. `GET /api/ready` is the other one: 503 until the
catalog warm-up has finished, which is what a platform's *startup* probe
should ask for. A warm-up that failed still reports ready, so a broken data
directory surfaces as a request error rather than a container that restarts
forever.

## Google Cloud Run

Cloud Run cannot pull from GHCR, so the image goes through Artifact Registry.
Mirroring the image CI already built and smoke-tested beats `--source .`, which
rebuilds all four stages on every deploy (re-fetching the Chummer data over the
network) and publishes something the tests never saw:

```bash
gcloud artifacts repositories create chummer --repository-format=docker \
  --location=asia-northeast1

# Cloud Run runs amd64 only, and `docker pull` takes the host's architecture —
# so pick the amd64 digest out of the multi-arch index and copy *that*.
crane manifest ghcr.io/<owner>/chummer-web:latest   # -> the linux/amd64 digest
crane copy ghcr.io/<owner>/chummer-web@sha256:<amd64> \
  asia-northeast1-docker.pkg.dev/<project>/chummer/chummer-web:latest

gcloud run deploy chummer-web \
  --image asia-northeast1-docker.pkg.dev/<project>/chummer/chummer-web@sha256:<amd64> \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 512Mi --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars TRUSTED_PROXY_HOPS=2 \
  --startup-probe httpGet.path=/api/ready,httpGet.port=8080,initialDelaySeconds=3,periodSeconds=5,timeoutSeconds=3,failureThreshold=12
```

Cloud Run sets `PORT`; the container already honours it. `timeoutSeconds` has
to be *less than* `periodSeconds` or the deploy is refused after the image is
already pushed.

**Point the startup probe at `/api/ready`, not `/api/health`.** `/api/health`
answers 200 as soon as uvicorn binds, which lets traffic in while the warm-up
thread is still parsing the data — the request then builds the catalog a second
time (`lru_cache` does not join concurrent callers) and the two compete for the
one vCPU. `/api/ready` is 503 until that warm-up has finished. Measured on one
vCPU in `asia-northeast1`, first request after 17-21 minutes idle:

| probe | first 200 | first `/api/catalog` | total |
| --- | --- | --- | --- |
| `/api/health`, `--cpu-boost` | 5.9 s | 5.1 s (4754 ms server-side) | ~11 s |
| `/api/health`, no boost | 10.4 s | 0.7 s (215 ms server-side) | ~11 s |
| `/api/ready`, no boost | 13.3 s | 0.77 s (90 ms server-side) | ~13 s |

The `/api/ready` probe is a trade, not a win on its own: the first visitor waits
~2.9 s longer, because Cloud Run now holds traffic until the warm-up has
actually finished instead of letting it in early and charging the difference to
whatever request arrives first. What it buys is that every request after that
first 200 is warm — the 90 ms server-side figure above is the double build gone.
It is worth taking **because the cron keepalive below means the cold path is
what happens when the keepalive has failed**, not what a normal visitor sees.
Without a keepalive, prefer `/api/health` with no boost.

- **`--cpu-boost` is not worth it here.** It takes 4.5 s off the container start
  and hands the same 4.5 s to the first catalog request; end to end the first
  two rows above are the same ~11 s. Building the catalog costs ~3.3 s on one
  Cloud Run vCPU against ~0.5 s on a developer machine.
- **`--min-instances 1`** is the only thing that removes the cold path
  entirely, and it bills the idle instance around the clock (roughly $10/month
  at this size). The cron keepalive is the cheaper approximation.
- **Memory**: measured peak is ~300 MiB, so `512Mi` fits with room and `1Gi` is
  the comfortable choice. Note that the container's writable paths are tmpfs and
  count against it.
- **`--max-instances 1`** — the rate limiter counts in process memory, so a
  second instance would hand out a second full allowance. It is also the cost
  ceiling.
- **Billing is per request** (CPU and memory only while a request is being
  handled, plus start-up), so a small group's use usually stays inside the
  monthly free tier.
- **Budget alert** — Billing › Budgets & alerts, e.g. $5 on the project. It has
  to be in the billing account's own currency; a USD amount on a JPY account is
  refused with a bare `INVALID_ARGUMENT`.
- **Custom domain** — `gcloud beta run domain-mappings create --service
  chummer-web --domain chummer.example.com --region asia-northeast1`, then add
  the DNS record it prints. On Cloudflare DNS, keep that record **DNS only**
  (grey cloud): Google issues the certificate and needs to see its own
  endpoint.
- **Organisation policy.** `--allow-unauthenticated` needs an `allUsers`
  binding, which an organisation enforcing *Domain restricted sharing*
  (`constraints/iam.allowedPolicyMemberDomains`) refuses — the deploy succeeds
  and then reports `Setting IAM policy failed`, leaving the service private.
  Either grant an exception on that project, or keep it private and use the
  Worker below.

**Do not put Cloudflare's proxy in front of a *public* service and set
`TRUST_CLOUDFLARE_IP=1`.** The `*.run.app` URL stays open to anyone, and a
caller going there directly writes `cf-connecting-ip` themselves — one request
per fake IP, past every limit. The next section is the shape where this becomes
safe, because there the service is not public at all.

## Cloud Run behind a Cloudflare Worker

The section above ends by saying you cannot have both Cloud Run and
Cloudflare's WAF without an external load balancer. There is one way, and it
is what `deploy/cloudflare-proxy/` does: leave the service **private** and let
a Worker be the only thing that can invoke it.

A private service is invoked with an OIDC identity token whose audience is the
service's URL. The Worker mints one from a service-account key (RFC 7523),
caches it for the hour it lasts, and forwards the request. So:

- `*.run.app` answers 403 to everyone. The hostname on your zone is the single
  route in, which is what the earlier warning was missing.
- Cloudflare's WAF, rate-limiting rules, Bot Fight Mode and Access sit in front
  of that single route. A domain mapping cannot do this: it must be grey-clouded
  because Google issues the certificate.
- `TRUST_CLOUDFLARE_IP=1` is sound here — nobody can reach the container with a
  forged `cf-connecting-ip`, because reaching it needs a token only the Worker
  can mint. Set `TRUSTED_PROXY_HOPS=0` with it.

It also keeps an organisation that enforces **Domain restricted sharing**
(`constraints/iam.allowedPolicyMemberDomains`) intact: that constraint refuses
an `allUsers` binding, and nothing here needs one.

```bash
# GCP: a service account that may invoke this one service, and nothing else
gcloud iam service-accounts create cf-worker --project "$PROJECT"
gcloud run services add-iam-policy-binding chummer-web --region asia-northeast1 \
  --member="serviceAccount:cf-worker@$PROJECT.iam.gserviceaccount.com" \
  --role=roles/run.invoker --project "$PROJECT"
gcloud iam service-accounts keys create key.json \
  --iam-account="cf-worker@$PROJECT.iam.gserviceaccount.com"

# Cloudflare
cd deploy/cloudflare-proxy
# edit wrangler.jsonc: routes[0].pattern -> your hostname, vars.RUN_URL -> the service URL
npm install
npx wrangler login
npx wrangler secret put GCP_SA_KEY < key.json   # then delete key.json
npx wrangler deploy
```

**Cold starts.** The Worker's cron trigger pings `/api/ready` every ten
minutes, which keeps one instance alive. Cloud Run bills while a request is
handled, not while an instance idles, so this costs a few seconds of compute a
day and saves every visitor after a quiet spell the ~11 s an instance takes to
come up. It is best effort — Cloud Run may reclaim an instance whenever it
likes, and a deploy replaces it — so it makes cold starts rare rather than
impossible. `--min-instances 1` is the version with a guarantee and a bill.

Bring it up on a spare hostname first (`cr.example.com`), confirm it, and only
then move the public name over — a rollback is then one route.

**The key is a long-lived credential.** Cloudflare has no OIDC issuer a Worker
could federate with, so there is no way to avoid one. Keep it in the Worker
secret only, never in the repository, and rotate it
(`gcloud iam service-accounts keys list / delete`). If that is the part you do
not want, Cloudflare Containers below needs no GCP at all.

## Fly.io

`fly launch` detects the Dockerfile. A minimal `fly.toml`:

```toml
app = "chummer-web"
primary_region = "nrt"

[build]

[env]
  TRUSTED_PROXY_HOPS = "2"   # rate-limit on the real client IP, not fly's edge

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0        # 1 for no cold starts

[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"

[checks.health]
  type = "http"
  path = "/api/health"
  interval = "30s"
  timeout = "3s"
```

## Cloudflare Containers

Everything on Cloudflare: a Worker takes the request and hands it to a container
running this same image. Needs the Workers Paid plan and a zone (your domain)
on the same account. Config lives in `deploy/cloudflare/`.

```bash
cd deploy/cloudflare
# edit wrangler.jsonc: routes[0].pattern -> your hostname
npm install
npx wrangler login
npx wrangler deploy        # builds the image locally with Docker, pushes, deploys
```

The image is built for `linux/amd64`. On an Apple Silicon Mac that runs under
emulation and the first build takes a long while; later ones reuse the cache.

What the config pins down, and why:

- **One instance** (`max_instances: 1`, and the Worker always asks for the
  instance named `main`). The rate limiter keeps its counters in process
  memory, so several containers would each hand out a full allowance. It is
  also the cost ceiling: nobody can make you run a second container.
- **`standard-1`** (1/2 vCPU, 4 GiB). `basic` fits in memory but makes the
  cold-start catalog parse slow.
- **`sleepAfter = "15m"`** — idle that long and it stops; billing is per
  running second, so a quiet instance costs little. Lengthen it to avoid cold
  starts, shorten it to pay less.
- **`TRUST_CLOUDFLARE_IP=1`** and the public rate limits (`120/minute`,
  `20/minute`) are set in `src/index.ts` (`envVars`), not `.env` — `.env` is
  only read by `docker compose`. The container is reachable only through the
  Worker, so `cf-connecting-ip` there is always Cloudflare's.
- **`workers_dev: false`, `preview_urls: false`** — the custom domain is the only
  public URL, so the WAF rules below cannot be walked around via
  `*.workers.dev`.

Logs: `npx wrangler tail`, or Workers & Pages › chummer-web › Logs in the
dashboard (the container writes JSON lines, `LOG_FORMAT=json`).

### Before going public

The app keeps no data (no accounts, characters stay in the browser), so the
realistic risk is someone burning CPU on your bill. In the dashboard, for the
zone:

1. **Security › WAF › Rate limiting rules** — one rule for
   `starts_with(http.request.uri.path, "/api/")`, e.g. 100 requests / 1 minute
   per IP → Block for 1 minute. This stops a flood at the edge, before it wakes
   the container. The app's own limits stay as the second line.
2. **Security › Bots** — turn on Bot Fight Mode.
3. **Billing › Billable usage notifications** — an alert for Workers /
   Containers usage, so a surprise shows up as an email, not an invoice.
4. **SSL/TLS** — mode *Full*, *Always Use HTTPS* on, minimum TLS 1.2.
5. **Small audience?** Put **Zero Trust › Access** on the hostname (e.g. email
   one-time PIN for your group). Anonymous visitors then never reach the
   Worker at all.
6. **Keep the image fresh.** Base images are pinned by digest; redeploy after
   taking the Dependabot / `make update` bumps, or security fixes in Python,
   Node and Caddy never reach the running container.

Sanity check afterwards: `curl -i https://<host>/api/health`, then fire
requests past the limit and confirm the 429 / log line shows your own IP.

## Self-host + Cloudflare Tunnel

Run the container (`docker compose up -d`), then point a named tunnel at it:

```
# ~/.cloudflared/config.yml
tunnel: <tunnel-id>
credentials-file: /home/you/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: chummer.example.com
    service: http://localhost:8080
  - service: http_status:404
```

Put **Cloudflare Access** in front if the audience is small — it removes the
anonymous-abuse surface entirely. Run the container on an isolated network
segment / dedicated device; the tunnel needs only outbound 443.

## Notes

- Single uvicorn worker. `compute()` is CPU-bound and runs in FastAPI's
  threadpool, so a handful of concurrent edits are fine on 1 vCPU. Bump with a
  custom `--workers N` in `deploy/supervisord.conf` if needed (each worker
  keeps its own `catalog()` cache → memory ×N).
- GPL-3.0: `LICENSE` and `NOTICE.txt` are in the image at `/app/`. Keep the
  repo reachable (public, or a source tarball) so users can get the source.
