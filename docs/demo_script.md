# 90-second demo video: script and shot list (task 8.10)

One real case, filmed on a phone against the live site. It is test case TC-02: a cashier in Abu Dhabi dismissed
without notice. The expected result is **AED 6,229.59**: notice pay 3,000.00 plus gratuity 3,229.59.

## Before you record (5 minutes)

1. **Wake the backend.** Open https://haqqi-api.onrender.com/healthz and wait until it shows `"status":"ok"`. The free
   Render plan sleeps, and the first request takes about a minute.
2. **Fresh Gemini quota.** Record after **11:00 UAE time** (07:00 UTC), when the free daily quota resets, so the case
   runs on Gemini in about 15–25 s.
3. **The phone:**
   - Turn on Do Not Disturb, set brightness high, and close other tabs.
   - Use iPhone **Control Centre → Screen Recording**, long-pressing it to turn the **microphone on** for narration.
   - If you'd rather narrate afterwards, record silently and add a voice-over in iMovie or CapCut.
4. Copy this story to your clipboard, so you can paste it if you don't want to speak it:

   > I worked as a cashier at a supermarket in Abu Dhabi. On 20 September my manager told me my job had ended
   > that day, with no notice. My contract says 30 days' notice. My basic salary is 2,000 dirhams and my total
   > salary is 3,000.

5. Do one practice run that you don't record.

## Shot list (about 90 s)

| Time | On screen (what you tap) | What you say |
| --- | --- | --- |
| 0–8 s | The home page, haqqi-ai.vercel.app | "Millions of migrant workers in the UAE don't know if their employer broke the law, or what they're owed. Haqqi tells them, in their own language." |
| 8–18 s | Scroll the language list slowly. Tap **اردو** (Urdu) to show the right-to-left layout, then go back and tap **English** | "It works in eight languages, including Hindi, Urdu, Malayalam and Arabic, by voice or text." |
| 18–32 s | On "What happened at work?": either tap **Speak your story** and say it, or paste it. Then tap **Continue** | "A worker just tells their story. Here, a cashier was dismissed with no notice." |
| 32–46 s | The confirm form. Check the pre-filled fields and fill any that are missing: **Abu Dhabi**, **Mainland**, **Company worker**, **Full time**, start **1 Jun 2024**, last day **20 Sep 2026**, basic **2000**, total **3000**, **My employer ended my job**, notice in contract **30**, notice given **0**. Tap **Check my case** | "Haqqi reads the facts from the story and asks the worker to confirm them, so nothing is guessed." |
| 46–56 s | The progress screen, with the steps ticking | "Four AI agents read the law, check each other's work, and write the answer. The law search runs over the full UAE labour law." |
| 56–76 s | The result: scroll slowly past the headline, a finding with its **Article 43** chip (tap it to open the law text), then the claim with its formulas and the **total AED 6,229.59**, then the 80084 disclaimer | "Every finding cites the exact article. Every amount comes from a calculator, not the AI, and shows its formula. That's notice pay plus gratuity: 6,229 dirhams." |
| 76–86 s | **Download complaint (PDF)** → **Save or share PDF** → open it. Show the Arabic letter beside the English translation | "And it writes a formal complaint to the Ministry in Arabic, ready to file, with a translation alongside." |
| 86–90 s | Back to the result, or the home page | "Haqqi. Know your rights, in your language." |

## Tips
- Keep it under 95 s. If you run long, shorten the language-picker shot first.
- If the result takes longer than about 30 s, the free Gemini quota is probably used up and a slower backup model
  answered. Stop and record again later; don't cut the wait out of the video.
- Don't use a real person's name or ID in the story or the complaint fields. Leave the name fields empty, or use
  "Test Worker".

## After recording
Upload it to YouTube as **Unlisted**, or attach it to a GitHub release, and send me the link. I'll add it to the
README (task 8.10).
