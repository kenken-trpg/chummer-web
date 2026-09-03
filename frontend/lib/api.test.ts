import { describe, expect, it } from "vitest";
import { errorText } from "@/lib/api";

function fakeResponse(
  body: string,
  contentType = "application/json",
  statusText = "Bad Request",
): Response {
  return {
    text: async () => body,
    headers: { get: (k: string) => (k.toLowerCase() === "content-type" ? contentType : null) },
    statusText,
  } as unknown as Response;
}

describe("errorText", () => {
  it("pulls FastAPI's {detail} string", async () => {
    expect(
      await errorText(fakeResponse(JSON.stringify({ detail: "この JSON を取り込めません" }))),
    ).toBe("この JSON を取り込めません");
  });

  it("joins a 422 detail array", async () => {
    const body = JSON.stringify({ detail: [{ msg: "field required" }, { msg: "too long" }] });
    expect(await errorText(fakeResponse(body))).toBe("field required / too long");
  });

  it("returns plain-text bodies as-is", async () => {
    expect(await errorText(fakeResponse("request body too large", "text/plain"))).toBe(
      "request body too large",
    );
  });

  it("falls back to the status line for an empty body", async () => {
    expect(await errorText(fakeResponse("", "application/json", "Gateway Timeout"))).toBe(
      "Gateway Timeout",
    );
  });
});
