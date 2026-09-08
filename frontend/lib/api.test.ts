import { beforeEach, describe, expect, it } from "vitest";
import { errorText } from "@/lib/api";
import { LOCALE_STORAGE_KEY } from "@/lib/i18n";

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
  beforeEach(() => window.localStorage.clear());

  it("renders our own {key, params} detail in the reader's locale", async () => {
    const body = JSON.stringify({
      detail: { key: "api.xmlUnparsable", params: { error: "line 3" } },
    });
    expect(await errorText(fakeResponse(body))).toBe("XML を解析できませんでした: line 3");

    window.localStorage.setItem(LOCALE_STORAGE_KEY, "en");
    expect(await errorText(fakeResponse(body))).toBe("The XML could not be parsed: line 3");
  });

  it("shows an unknown key as itself rather than blanking the message", async () => {
    const body = JSON.stringify({ detail: { key: "api.fromANewerBackend" } });
    expect(await errorText(fakeResponse(body))).toBe("api.fromANewerBackend");
  });

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
