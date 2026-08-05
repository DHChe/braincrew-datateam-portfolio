import { expect, test, type Page } from "@playwright/test";

async function openWithStaticAssetGuard(page: Page, path: string) {
  const failedStaticAssets: string[] = [];
  page.on("response", (response) => {
    const pathname = new URL(response.url()).pathname;
    const contentType = response.headers()["content-type"] ?? "";

    if (
      pathname.includes("/_next/") &&
      (response.status() >= 400 || contentType.includes("text/html"))
    ) {
      failedStaticAssets.push(
        `${response.status()} ${contentType || "missing content-type"} ${pathname}`,
      );
    }
  });

  await page.goto(path, { waitUntil: "networkidle" });

  expect(failedStaticAssets).toEqual([]);
}

test("the Korean page states the fixture boundary and renders artifact values untranslated", async ({
  page,
}) => {
  await openWithStaticAssetGuard(page, "./ko/");

  await expect(
    page.getByText("고정 예제(fixture) 근거 — 라이브 AX 검증 결과가 아닙니다", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByTestId("live-comparison-boundary")).toContainText(
    "이 PASS는 고정 예제 게이트의 결과이며 라이브 릴리스 판정이 아닙니다.",
  );

  // Artifact values are rendered as exported, in either locale.
  await expect(page.getByTestId("canonical-decision")).toHaveText("PASS");
  await expect(page.getByTestId("release-gate")).toHaveCount(3);
  await expect(page.getByTestId("logical-digest")).toContainText(
    "d426e04c0c2b960d8c8c17efc216688891b2078faaaa51ff226c137c2f8694ae",
  );

  await expect(page.locator("main")).toHaveAttribute("lang", "ko");
});

test("each locale links to the other", async ({ page }) => {
  await openWithStaticAssetGuard(page, "./ko/");

  await page.getByRole("link", { name: "English" }).click();
  await expect(
    page.getByRole("heading", { name: "Release evidence, without the rerun." }),
  ).toBeVisible();

  await page.getByRole("link", { name: "한국어" }).click();
  await expect(page.locator("main")).toHaveAttribute("lang", "ko");
});
