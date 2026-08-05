import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { DashboardExplorer } from "../../dashboard/components/dashboard-explorer";
import { koCopy, type Locale } from "../../dashboard/lib/copy";
import { dashboardData } from "../../dashboard/lib/dashboard-data";

describe("DashboardExplorer", () => {
  it("omits the fixture-only live-comparison reason for live evidence", () => {
    const liveData = {
      ...dashboardData,
      baseline: { ...dashboardData.baseline, execution_mode: "live" as const },
      candidate: {
        ...dashboardData.candidate,
        execution_mode: "live" as const,
      },
    };

    const markup = renderToStaticMarkup(
      createElement(DashboardExplorer, { data: liveData, locale: "en" }),
    );

    expect(markup).toContain("Live verification evidence");
    expect(markup).not.toContain(
      "This PASS is a fixture-gate result, not a live release verdict",
    );
  });

  it("states the fixture boundary in Korean on the Korean locale", () => {
    const markup = renderToStaticMarkup(
      createElement(DashboardExplorer, { data: dashboardData, locale: "ko" }),
    );

    expect(markup).toContain(koCopy.fixtureEvidenceLabel);
    expect(markup).toContain(koCopy.fixtureBoundaryReason);
    expect(markup).toContain('lang="ko"');
  });

  it("renders artifact values untranslated in both locales", () => {
    const untranslated = [
      dashboardData.decision,
      dashboardData.logical_digest,
      "Compatibility",
      "Quality &amp; safety",
      "Operational",
    ];

    for (const locale of ["en", "ko"] as Locale[]) {
      const markup = renderToStaticMarkup(
        createElement(DashboardExplorer, { data: dashboardData, locale }),
      );

      for (const value of untranslated) {
        expect(markup, `${locale}: ${value}`).toContain(value);
      }
    }
  });

  it("links each locale to the other", () => {
    const english = renderToStaticMarkup(
      createElement(DashboardExplorer, { data: dashboardData, locale: "en" }),
    );
    const korean = renderToStaticMarkup(
      createElement(DashboardExplorer, { data: dashboardData, locale: "ko" }),
    );

    expect(english).toContain("한국어");
    expect(korean).toContain("English");
  });
});
