import { render, screen } from "@testing-library/react";
import { AppFooter, AUTHOR, MANUAL_URL, REPO_URL } from "@/components/character/AppFooter";

describe("<AppFooter>", () => {
  it("credits the author and links the repository", () => {
    render(<AppFooter />);
    const link = screen.getByRole("link", { name: "GitHub リポジトリ" });
    expect(link.getAttribute("href")).toBe(REPO_URL);
    // opening a new tab without this hands the opener to the other page
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
    expect(screen.getByText(`制作: ${AUTHOR}`)).toBeDefined();
  });

  it("links the manual, which is a static page rather than a route", () => {
    render(<AppFooter />);
    const link = screen.getByRole("link", { name: "使い方" });
    // `next.config.ts` rewrites this to `public/manual/index.html`
    expect(link.getAttribute("href")).toBe(MANUAL_URL);
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });
});
