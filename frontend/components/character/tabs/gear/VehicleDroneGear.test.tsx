import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { VehicleDroneGear } from "@/components/character/tabs/gear/VehicleDroneGear";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

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
      {...panelProps(ch, {
        catalog:
          over.catalog ?? makeCatalog({ drones: [drone] as never, vehicles: [vehicle] as never }),
        patch: over.patch ?? (() => {}),
      })}
      mode={mode}
    />,
  );
}

describe("<VehicleDroneGear>", () => {
  it("spells out the vehicle stat abbreviations", () => {
    const owned = { ...vehicle, accel: 2, body: 11, armor: 6, pilot: 1, sensor: 2, nuyen: 16000 };
    const ch = makeCharacter({ vehicles: [owned], derived: { vehicles: [owned] } } as never);
    const { container } = render(
      <VehicleDroneGear
        {...panelProps(ch, {
          catalog: makeCatalog({ drones: [drone] as never, vehicles: [vehicle] as never }),
          patch: () => {},
        })}
        mode="vehicle"
      />,
    );
    const button = container.querySelector(".muted button") as HTMLElement;
    const tip = document.getElementById(button.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("HND 操縦性");
    expect(tip?.textContent).toContain("PLT はオートパイロット");
  });

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
