import { creationBudgets } from "./creation-review";
import { makeCharacter } from "@/tests/fixtures";

it("uses engine budgets including zero and overdrawn points", () => {
  const ch = makeCharacter({
    derived: {
      points: { attributes: { used: 10, max: 12 }, skills: { used: 6, max: 5 } } as never,
      karma: { remaining: 0, pool: 25, spent: 25 },
      nuyen: 500,
      contact_points: { free: 3, used: 5 } as never,
    },
  });
  const budgets = creationBudgets(ch);
  expect(budgets.find((row) => row.label === "check.points.attributes")?.remaining).toBe(2);
  expect(budgets.find((row) => row.label === "check.points.skills")?.remaining).toBe(-1);
  expect(budgets.find((row) => row.label === "app.creationReview.karma")?.remaining).toBe(0);
  expect(budgets.find((row) => row.label === "app.creationReview.contacts")?.remaining).toBe(0);
});

it("shows free magical slots separately from paid purchases and respects enabled tabs", () => {
  const ch = makeCharacter({
    derived: {
      enabled_tabs: ["spells", "adept"],
      spell_points: { free: 5, used: 7, paid: 2 },
      complex_form_points: { free: 2, used: 1, paid: 0 },
      power_points: { max: 6, used: 5.5 },
    },
  });
  const budgets = creationBudgets(ch);
  expect(budgets.find((row) => row.label === "app.creationReview.spells")?.remaining).toBe(0);
  expect(budgets.find((row) => row.label === "app.creationReview.power")?.remaining).toBe(0.5);
  expect(budgets.some((row) => row.label === "app.creationReview.forms")).toBe(false);
});
