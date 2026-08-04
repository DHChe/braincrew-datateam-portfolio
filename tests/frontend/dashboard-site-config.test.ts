import { describe, expect, it } from "vitest";

import { pagesBasePath } from "../../dashboard/site-config.cjs";

describe("dashboard site configuration", () => {
  it("keeps the runtime Pages path at the declared project path", () => {
    expect(pagesBasePath).toBe("/evidence-first-rag-evaluation");
  });
});
