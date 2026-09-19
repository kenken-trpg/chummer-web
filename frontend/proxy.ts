import { NextResponse, type NextRequest } from "next/server";
import { REPORT_ENDPOINT, REPORT_GROUP, contentSecurityPolicy, makeNonce } from "@/lib/csp";

/**
 * Mint a nonce for every page and put the CSP that names it on both the
 * request (Next reads it there while rendering, to stamp the nonce on its own
 * script tags) and the response (the browser enforces it there).
 *
 * This is the only place the page CSP is set. `next.config.ts` used to send a
 * static one and `deploy/Caddyfile` another; both said `'unsafe-inline'` for
 * scripts, because a static header cannot carry a per-request nonce.
 */
export function proxy(request: NextRequest) {
  const nonce = makeNonce();
  const csp = contentSecurityPolicy(nonce, { dev: process.env.NODE_ENV === "development" });

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  // Declares the group the CSP's `report-to` names. Only on the response: the
  // browser reads it there, and it says nothing to the renderer.
  response.headers.set(
    "Reporting-Endpoints",
    `${REPORT_GROUP}="${new URL(REPORT_ENDPOINT, request.nextUrl.origin).toString()}"`,
  );
  return response;
}

export const config = {
  matcher: [
    {
      // Documents only. `/api` is FastAPI's and sets its own, stricter policy;
      // static files and prefetches are not documents, and a CSP does nothing
      // for a response the browser never renders as a page.
      source: "/((?!api|_next/static|_next/image|favicon.ico).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
