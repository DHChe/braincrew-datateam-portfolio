import { expect, test } from "@playwright/test";

test("renders the immutable comparison and its three-gate decision trace", async ({
  page,
}) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Release evidence, without the rerun." }),
  ).toBeVisible();
  await expect(page.getByTestId("canonical-decision")).toHaveText("PASS");
  await expect(page.getByText("15 publishable cases")).toBeVisible();
  await expect(page.getByText("6 canonical metrics")).toBeVisible();
  await expect(
    page.getByText("Fixture evidence — not a live AX verification"),
  ).toBeVisible();
  await expect(page.getByTestId("logical-digest")).toContainText(
    "f8630e70892f976ee120ac497ef63ce6cc64add8aa1d71989a576891b5ae7bbe",
  );
  await expect(page.getByTestId("release-gate")).toHaveCount(3);
  await expect(
    page.getByRole("row", { name: /claim support precision/i }),
  ).toContainText("+0.03");
});

test("drills into metric, taxonomy, and publishable case evidence without executing experiments", async ({
  page,
}) => {
  await page.goto("/");

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
