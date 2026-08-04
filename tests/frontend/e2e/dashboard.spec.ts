import { expect, test, type Page } from "@playwright/test";

async function openDashboardWithStaticAssetGuard(page: Page) {
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

  await page.goto("./", { waitUntil: "networkidle" });

  expect(failedStaticAssets).toEqual([]);
}

test("renders the immutable comparison and its three-gate decision trace", async ({
  page,
}) => {
  await openDashboardWithStaticAssetGuard(page);

  await expect(
    page.getByRole("heading", { name: "Release evidence, without the rerun." }),
  ).toBeVisible();
  await expect(page.getByTestId("canonical-decision")).toHaveText("PASS");
  await expect(page.getByText("15 publishable cases")).toBeVisible();
  await expect(page.getByText("6 canonical metrics")).toBeVisible();
  await expect(
    page.getByText("Fixture evidence — not a live AX verification", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByTestId("live-comparison-boundary")).toContainText(
    "This PASS is a fixture-gate result, not a live release verdict: both same-commit live runs are INVALID after 13 of 15 grounded answers were discarded for citation-contract violations, leaving no answer-quality evidence.",
  );
  await expect(
    page.getByRole("link", { name: "Decision record" }),
  ).toHaveAttribute(
    "href",
    "https://github.com/DHChe/evidence-first-rag-evaluation/blob/develop/docs/decisions/2026-08-03-same-commit-30-case-run-and-grounded-coverage-correction.md",
  );
  await expect(page.getByTestId("logical-digest")).toContainText(
    "d426e04c0c2b960d8c8c17efc216688891b2078faaaa51ff226c137c2f8694ae",
  );
  await expect(page.getByTestId("release-gate")).toHaveCount(3);
  await expect(
    page.getByRole("row", { name: /claim support precision/i }),
  ).toContainText("+0.03");
});

test("drills into metric, taxonomy, and publishable case evidence without executing experiments", async ({
  page,
}) => {
  await openDashboardWithStaticAssetGuard(page);

  await page.getByRole("tab", { name: "Case evidence" }).click();
  await page.getByLabel("Find case evidence").fill("CASE-001");
  await expect(page.getByText("CASE-001", { exact: true })).toBeVisible();
  await expect(page.getByText("CASE-002", { exact: true })).not.toBeVisible();
  await page.locator("summary", { hasText: "CASE-001" }).click();
  await expect(page.getByTestId("case-detail-CASE-001")).toContainText(
    "claim support precision",
  );

  await page.getByRole("tab", { name: "Failure taxonomy" }).click();
  await expect(
    page.getByText("No candidate failures in this verified artifact."),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /run experiment/i }),
  ).toHaveCount(0);
});
