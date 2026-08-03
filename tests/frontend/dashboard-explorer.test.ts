import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { DashboardExplorer } from "../../dashboard/components/dashboard-explorer";
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
      createElement(DashboardExplorer, { data: liveData }),
    );

    expect(markup).toContain("Live verification evidence");
    expect(markup).not.toContain(
      "This PASS is a fixture-gate result, not a live release verdict",
    );
  });
});
