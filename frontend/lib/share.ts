/**
 * Saving the complaint PDF on phones (task 5.5). iOS Safari ignores `<a download>` for a blob and
 * opens the PDF in its viewer, so phones get the system share sheet (Save to Files, WhatsApp, Print).
 * `navigator.share` needs a fresh tap, so it is called from its own button once the file is ready.
 */

type ShareNavigator = Pick<Navigator, "canShare" | "share">;

export function pdfFile(blob: Blob, name: string): File {
  return new File([blob], name, { type: "application/pdf" });
}

export function canShareFile(file: File, nav: Partial<ShareNavigator> | undefined = globalThis.navigator): boolean {
  try {
    return Boolean(nav?.canShare && nav.share && nav.canShare({ files: [file] }));
  } catch {
    return false;
  }
}

/** Opens the share sheet. Closing it is not an error. */
export async function shareFile(file: File, nav: ShareNavigator = globalThis.navigator): Promise<"shared" | "cancelled"> {
  try {
    await nav.share({ files: [file], title: file.name });
    return "shared";
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") return "cancelled";
    throw err;
  }
}

/** Desktop browsers: a normal download. */
export function saveFile(file: File) {
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = file.name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // iOS Safari reads the URL after click() returns; revoke it later.
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
