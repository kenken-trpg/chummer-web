import { render, screen } from "@testing-library/react";
import { AppFooter, AUTHOR, REPO_URL } from "@/components/character/AppFooter";

describe("<AppFooter>", () => {
  it("credits the author and links the repository", () => {
    render(<AppFooter />);
    const link = screen.getByRole("link", { name: "GitHub リポジトリ" });
    expect(link.getAttribute("href")).toBe(REPO_URL);
    // opening a new tab without this hands the opener to the other page
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
    expect(screen.getByText(`制作: ${AUTHOR}`)).toBeDefined();
  });
});
