import { describe, expect, it } from "vitest";
import type { Character } from "@/lib/types";
import { careerFloor, careerSpecLocked } from "./career-floor";

const ch = (over: Partial<Character>) => ({ attributes: {}, ...over }) as Character;

describe("careerFloor", () => {
  it("is the rating held on entering career", () => {
    const c = ch({
      career: true,
      career_baseline: { attributes: { BOD: 3 }, skills: { Pistols: 4 } },
    });
    expect(careerFloor(c, "attributes", "BOD")).toBe(3);
    expect(careerFloor(c, "skills", "Pistols")).toBe(4);
  });

  it("is 0 for what the baseline does not hold, and outside career", () => {
    const c = ch({ career: true, career_baseline: { skills: { Pistols: 4 } } });
    expect(careerFloor(c, "skills", "Sneaking")).toBe(0);
    expect(careerFloor(ch({ career: true }), "skills", "Pistols")).toBe(0);
    expect(
      careerFloor(
        ch({ career: false, career_baseline: { skills: { Pistols: 4 } } }),
        "skills",
        "Pistols",
      ),
    ).toBe(0);
  });
});

describe("careerSpecLocked", () => {
  it("holds a specialization the baseline recorded, in career only", () => {
    const base = { career_baseline: { skill_specializations: ["Blades"] } };
    expect(careerSpecLocked(ch({ career: true, ...base }), "Blades")).toBe(true);
    expect(careerSpecLocked(ch({ career: true, ...base }), "Pistols")).toBe(false);
    expect(careerSpecLocked(ch({ career: false, ...base }), "Blades")).toBe(false);
  });
});
