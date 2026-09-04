import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { VehicleDroneGear } from "@/components/character/tabs/gear/VehicleDroneGear";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const drone = {
  id: "fly",
  name: "MCT Fly-Spy",
  category: "Drones: Micro",
  handling: 4,
  speed: 3,
  pilot: 3,
  sensor: 3,
  cost: 2000,
  avail: "4",
  source: "SR5",
};
const vehicle = {
  id: "americar",
  name: "Ford Americar",
  category: "Cars",
  handling: 4,
  speed: 3,
  seats: 4,
  cost: 16000,
  avail: "4",
  source: "SR5",
};

function renderTab(
  mode: "drone" | "vehicle",
  over: {
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter();
  return render(
    <VehicleDroneGear
      catalog={over.catalog ?? makeCatalog({ drones: [drone] as any, vehicles: [vehicle] as any })}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
      mode={mode}
    />,
  );
}

describe("<VehicleDroneGear>", () => {
  it("shows the drone search + list in drone mode and buys via patch", () => {
    const patch = vi.fn();
    renderTab("drone", { patch });
    expect(screen.getByPlaceholderText("ドローンを検索")).toBeDefined();
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("MCT Fly-Spy"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({ drones: [{ gear_id: "fly" }] });
  });

  it("shows the vehicle search + list in vehicle mode and buys via patch", () => {
    const patch = vi.fn();
    renderTab("vehicle", { patch });
    expect(screen.getByPlaceholderText("車両を検索")).toBeDefined();
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Ford Americar"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({ vehicles: [{ gear_id: "americar" }] });
  });
});
