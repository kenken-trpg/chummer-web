import { describe, expect, it } from "vitest";
import { makeTr, scopeTr } from "@/lib/ui-strings";

const catalog = {
  translations: { Binding: "接着", Medicine: "医学", Ork: "オーク" },
  translations_by_kind: {
    skill: { Binding: "束縛", Medicine: "医術" },
    knowledge_skill: { Sioux: "スー語" },
  },
};

describe("scopeTr", () => {
  it("prefers the kind's reading over the flat table", () => {
    const tr = makeTr(catalog);
    expect(tr("Binding")).toBe("接着");
    expect(scopeTr(tr, "skill")("Binding")).toBe("束縛");
    expect(scopeTr(tr, "knowledge_skill")("Medicine")).toBe("医学");
  });

  it("falls through to the flat table for names the kind does not list", () => {
    expect(scopeTr(makeTr(catalog), "skill")("Ork")).toBe("オーク");
  });

  it("finds a name the flat table leaves in English", () => {
    expect(scopeTr(makeTr(catalog), "knowledge_skill")("Sioux")).toBe("スー語");
  });

  it("tries a nested scope's kinds first, then its parent's", () => {
    const outer = scopeTr(makeTr(catalog), "knowledge_skill");
    const inner = scopeTr(outer, "skill");
    expect(inner("Binding")).toBe("束縛");
    expect(inner("Sioux")).toBe("スー語");
  });

  it("leaves English alone, and a plain function unchanged", () => {
    expect(scopeTr(makeTr(catalog, "en"), "skill")("Binding")).toBe("Binding");
    const plain = (name: string) => name;
    expect(scopeTr(plain, "skill")).toBe(plain);
  });
});
