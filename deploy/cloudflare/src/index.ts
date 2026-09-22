import { Container } from "@cloudflare/containers";

interface Env {
  CHUMMER: DurableObjectNamespace<ChummerContainer>;
}

export class ChummerContainer extends Container<Env> {
  // Caddy inside the image (deploy/Caddyfile).
  defaultPort = 8080;
  // Idle this long and the container stops; the next request pays a cold start.
  sleepAfter = "15m";
  envVars = {
    // The Worker forwards the visitor's request, `cf-connecting-ip` included,
    // and nothing but this Worker can reach the container, so the header is
    // Cloudflare's own. Rate limits then count real visitors, not the Worker.
    TRUST_CLOUDFLARE_IP: "1",
    // Public-instance limits (docs/deploy.md › Runtime env), not the loose
    // single-user values in .env.example.
    RATE_LIMIT: "120/minute",
    IMPORT_RATE_LIMIT: "20/minute",
    LOG_FORMAT: "json",
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // A single named instance: slowapi's counters live in process memory, so
    // spreading requests over several containers would multiply every limit.
    return env.CHUMMER.getByName("main").fetch(request);
  },
} satisfies ExportedHandler<Env>;
