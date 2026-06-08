import { describe, expect, it } from "vitest";

import { formatBytes, shortenText } from "../presenter";

describe("presenter helpers", () => {
  it("formats byte sizes for ui display", () => {
    expect(formatBytes(2048)).toBe("2.0 KB");
  });

  it("shortens long text with head and tail segments", () => {
    expect(shortenText("abcdefghijklmnop", 4, 4)).toBe("abcd...mnop");
  });
});
