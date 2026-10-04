import { describe, expect, it, vi } from "vitest";

import { canShareFile, pdfFile, shareFile } from "./share";

const file = pdfFile(new Blob(["%PDF-1.7"]), "haqqi-complaint.pdf");

describe("complaint file sharing", () => {
  it("makes a named PDF file", () => {
    expect(file.name).toBe("haqqi-complaint.pdf");
    expect(file.type).toBe("application/pdf");
  });

  it("offers sharing only where the browser can share files", () => {
    const share = vi.fn();
    expect(canShareFile(file, { canShare: () => true, share })).toBe(true);
    expect(canShareFile(file, { canShare: () => false, share })).toBe(false);
    expect(canShareFile(file, { share })).toBe(false); // desktop Firefox: no canShare
    expect(canShareFile(file, undefined)).toBe(false);
    expect(
      canShareFile(file, {
        canShare: () => {
          throw new TypeError("files not supported");
        },
        share,
      }),
    ).toBe(false);
  });

  it("shares the file, and treats closing the sheet as cancelled", async () => {
    const share = vi.fn().mockResolvedValue(undefined);
    expect(await shareFile(file, { canShare: () => true, share })).toBe("shared");
    expect(share).toHaveBeenCalledWith({ files: [file], title: "haqqi-complaint.pdf" });

    const closed = vi.fn().mockRejectedValue(new DOMException("closed", "AbortError"));
    expect(await shareFile(file, { canShare: () => true, share: closed })).toBe("cancelled");

    const denied = vi.fn().mockRejectedValue(new DOMException("no", "NotAllowedError"));
    await expect(shareFile(file, { canShare: () => true, share: denied })).rejects.toThrow("no");
  });
});
