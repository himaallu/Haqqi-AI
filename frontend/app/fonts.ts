import {
  Noto_Nastaliq_Urdu,
  Noto_Sans,
  Noto_Sans_Arabic,
  Noto_Sans_Bengali,
  Noto_Sans_Devanagari,
  Noto_Sans_Malayalam,
} from "next/font/google";

// Downloaded at build time and served from our own domain: no request to Google from the worker's phone.
// Script fonts aren't preloaded; the browser fetches one only when its characters (unicode-range) appear.
const notoSans = Noto_Sans({ subsets: ["latin"], variable: "--font-noto-sans", display: "swap" });
const devanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-noto-devanagari", display: "swap", preload: false });
const bengali = Noto_Sans_Bengali({ subsets: ["bengali"], variable: "--font-noto-bengali", display: "swap", preload: false });
const malayalam = Noto_Sans_Malayalam({ subsets: ["malayalam"], variable: "--font-noto-malayalam", display: "swap", preload: false });
const arabic = Noto_Sans_Arabic({ subsets: ["arabic"], variable: "--font-noto-arabic", display: "swap", preload: false });
const nastaliq = Noto_Nastaliq_Urdu({ subsets: ["arabic"], variable: "--font-noto-nastaliq", display: "swap", preload: false });

export const fontVariables = [notoSans, devanagari, bengali, malayalam, arabic, nastaliq]
  .map((f) => f.variable)
  .join(" ");
