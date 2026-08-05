import { describe, expect, it } from "vitest";

import { enCopy, koCopy, type DashboardCopy } from "../../dashboard/lib/copy";

/**
 * Keys whose English and Korean values are deliberately identical. Everything
 * else must differ, so a key added to one locale and copy-pasted into the other
 * fails here instead of shipping an untranslated string to readers.
 */
const INTENTIONALLY_SHARED = new Set<keyof DashboardCopy>([
  "comparisonEyebrowLabel",
]);

describe("dashboard copy", () => {
  it("defines the same keys in both locales", () => {
    expect(Object.keys(koCopy).sort()).toEqual(Object.keys(enCopy).sort());
  });

  it("leaves no empty string in either locale", () => {
    for (const copy of [enCopy, koCopy]) {
      for (const [key, value] of Object.entries(copy)) {
        if (typeof value === "string") {
          expect(value.trim(), key).not.toBe("");
        }
      }
    }
  });

  it("translates every string except the deliberately shared ones", () => {
    for (const key of Object.keys(enCopy) as (keyof DashboardCopy)[]) {
      const english = enCopy[key];
      const korean = koCopy[key];
      if (typeof english !== "string" || typeof korean !== "string") continue;
      if (INTENTIONALLY_SHARED.has(key)) {
        expect(korean, key).toBe(english);
      } else {
        expect(korean, key).not.toBe(english);
      }
    }
  });

  it("renders counts through locale-specific templates", () => {
    expect(enCopy.publishableCases(15)).toBe("15 publishable cases");
    expect(enCopy.canonicalMetrics(6)).toBe("6 canonical metrics");
    expect(enCopy.caseFailures(0)).toBe("0 failures");
    expect(koCopy.publishableCases(15)).toBe("공개 가능 사례 15건");
    expect(koCopy.canonicalMetrics(6)).toBe("정규 지표 6개");
    expect(koCopy.caseFailures(0)).toBe("실패 0건");
  });

  it("points each locale at the other", () => {
    expect(enCopy.htmlLang).toBe("en");
    expect(koCopy.htmlLang).toBe("ko");
    expect(enCopy.altLocalePath).toBe("/ko/");
    expect(koCopy.altLocalePath).toBe("/");
  });

  it("keeps the fixture boundary explicit in Korean", () => {
    expect(koCopy.fixtureEvidenceLabel).toContain(
      "라이브 AX 검증 결과가 아닙니다",
    );
    expect(koCopy.fixtureBoundaryReason).toContain("INVALID");
    expect(koCopy.fixtureBoundaryReason).toContain(
      "라이브 릴리스 판정이 아닙니다",
    );
  });
});
