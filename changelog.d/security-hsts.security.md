- **The public site asks browsers to come back over HTTPS only.** The
  Cloudflare Worker in front of Cloud Run adds `Strict-Transport-Security`,
  starting at five minutes so a mistake cannot stick. Self-hosted copies are
  unaffected: the header is set at the production edge alone.
