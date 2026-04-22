// ─────────────────────────────────────────
// REVERIE — sleepEngine.js
// Pure bedtime calculation logic.
// No DOM, no Firebase — import anywhere and test directly.
// All clock values are "HH:MM" strings (24-hour). Internal arithmetic uses
// integer minutes from midnight (0–1439).
// ─────────────────────────────────────────

// ── Defaults applied when a profile field is missing ──
export const SLEEP_DEFAULTS = {
  wakeTime:         "07:00",
  chronotype:       "middle",   // "early" | "middle" | "night"
  desiredSleepHours: null,      // if null, falls back to age-based guideline
  age:              null,
  caffeineLastCup:  null,       // "HH:MM" of last caffeinated drink today, or null
  exerciseTiming:   "none",     // "morning" | "afternoon" | "evening" | "none"
  napsDaily:        false,
  napDuration:      20,         // minutes
  screenCutoffMins: 60,         // minutes of screen-free time before bed
  stressLevel:      2,          // 1 (low) – 5 (high)
  alcoholNightly:   false,
  shiftWork:        false,
};

// ── Helpers ──────────────────────────────

// "HH:MM" → integer minutes from midnight (null on bad input)
export function timeToMinutes(time) {
  if (!time || typeof time !== "string") return null;
  const [h, m] = time.split(":").map(Number);
  if (isNaN(h) || isNaN(m)) return null;
  return h * 60 + m;
}

// Integer minutes (any range) → "HH:MM" string, normalized to 0–1439
export function minutesToTime(minutes) {
  const norm = ((minutes % 1440) + 1440) % 1440;
  const h = Math.floor(norm / 60);
  const m = norm % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

// "HH:MM" 24-hour → "10:30 PM" display format
export function formatTime12h(time24) {
  const mins = timeToMinutes(time24);
  if (mins === null) return time24;
  const h24  = Math.floor(mins / 60);
  const m    = mins % 60;
  const ampm = h24 < 12 ? "AM" : "PM";
  const h12  = h24 % 12 || 12;
  return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
}

// Age → recommended sleep hours (CDC / AASM guidelines).
// Used only when desiredSleepHours is not provided.
export function ageToSleepHours(age) {
  if (!age || age < 0) return 8;
  if (age <= 13)  return 10;
  if (age <= 17)  return 9;
  if (age <= 25)  return 8.5;
  if (age <= 64)  return 8;
  return 7.5;
}

// Merge caller's profile with defaults so downstream code never sees undefined
export function applyDefaults(profile = {}) {
  return { ...SLEEP_DEFAULTS, ...profile };
}

// ── Main calculation ──────────────────────

/**
 * calculateBedtime(rawProfile)
 *
 * Returns:
 *   bedtime          — recommended bedtime "HH:MM"
 *   bedtimeRange     — { early, late } ±30 min window
 *   targetSleepHours — hours the recommendation is built around
 *   adjustments      — array of { factor, delta (minutes), note }
 *                      delta > 0 = pushed later, delta < 0 = pulled earlier
 */
export function calculateBedtime(rawProfile) {
  const p = applyDefaults(rawProfile);

  // ── 1. Target sleep duration ──────────────
  // desiredSleepHours is the primary source; age is the fallback.
  const targetSleepHours = p.desiredSleepHours
    ? Number(p.desiredSleepHours)
    : ageToSleepHours(p.age);

  // ── 2. Base bedtime ───────────────────────
  const wakeMins = timeToMinutes(p.wakeTime) ?? timeToMinutes(SLEEP_DEFAULTS.wakeTime);
  let bed = wakeMins - targetSleepHours * 60;
  // bed can be negative (e.g. wake 7am - 8h = -60 = 11pm previous night).
  // We work in raw minutes throughout and normalise only at the end.

  const adjustments = [];

  // ── 3. Chronotype ─────────────────────────
  if (p.chronotype === "night") {
    bed += 30;
    adjustments.push({ factor: "Chronotype", delta: +30, note: "Night owls naturally fall asleep later — shifted 30 min later" });
  } else if (p.chronotype === "early") {
    bed -= 30;
    adjustments.push({ factor: "Chronotype", delta: -30, note: "Early birds naturally fall asleep earlier — shifted 30 min earlier" });
  }

  // ── 4. Caffeine ───────────────────────────
  // Caffeine has a ~6-hour half-life. If bedtime falls within the active
  // window, push it back until after clearance.
  if (p.caffeineLastCup) {
    const caffMins = timeToMinutes(p.caffeineLastCup);
    if (caffMins !== null) {
      const clearBy = caffMins + 360;                            // 6h clearance
      const bedNorm = ((bed % 1440) + 1440) % 1440;             // normalise for compare
      // clearBy may exceed 1440 (e.g. coffee at 10 pm, clears at 4 am).
      // The 600-min cap prevents false positives from wraparound arithmetic.
      if (clearBy > bedNorm && clearBy - bedNorm < 600) {
        const push = clearBy - bedNorm;
        bed += push;
        adjustments.push({
          factor: "Caffeine",
          delta:  push,
          note:   `Last caffeine at ${formatTime12h(p.caffeineLastCup)} — needs until ~${formatTime12h(minutesToTime(clearBy))} to clear`,
        });
      }
    }
  }

  // ── 5. Evening exercise ───────────────────
  // Raises core temperature; needs ~2 h to drop before quality sleep.
  if (p.exerciseTiming === "evening") {
    bed += 30;
    adjustments.push({ factor: "Exercise", delta: +30, note: "Evening workouts raise core temperature — allow extra wind-down time" });
  }

  // ── 6. Screen exposure ────────────────────
  // Blue light suppresses melatonin onset. < 30 min screen-free = meaningful delay.
  if (typeof p.screenCutoffMins === "number" && p.screenCutoffMins < 30) {
    bed += 20;
    adjustments.push({ factor: "Screens", delta: +20, note: "Less than 30 min screen-free time before bed delays melatonin — try cutting off 30+ min earlier" });
  }

  // ── 7. Naps ──────────────────────────────
  // Naps > 30 min reduce homeostatic sleep pressure, pushing natural bedtime later.
  if (p.napsDaily && Number(p.napDuration) > 30) {
    bed += 20;
    adjustments.push({ factor: "Naps", delta: +20, note: `${p.napDuration}-min nap reduces sleep drive — bedtime shifts later` });
  }

  // ── 8. Stress ─────────────────────────────
  // High stress increases sleep-onset latency. Starting wind-down earlier compensates.
  if (Number(p.stressLevel) >= 4) {
    bed -= 20;
    adjustments.push({ factor: "Stress", delta: -20, note: "High stress slows sleep onset — start wind-down routine 20 min earlier than this target" });
  }

  // ── 9. Alcohol ────────────────────────────
  // Alcohol reduces REM and deep sleep. An earlier start partially compensates
  // for reduced sleep quality.
  if (p.alcoholNightly) {
    bed -= 30;
    adjustments.push({ factor: "Alcohol", delta: -30, note: "Alcohol reduces sleep quality — going to bed earlier partially compensates" });
  }

  // ── 10. Shift work ────────────────────────
  // Flag only — no mechanical adjustment, but worth surfacing.
  if (p.shiftWork) {
    adjustments.push({ factor: "Shift work", delta: 0, note: "Irregular schedules disrupt circadian rhythm — anchor your wake time even on days off when possible" });
  }

  // ── Normalise ────────────────────────────
  const bedNormFinal = ((bed % 1440) + 1440) % 1440;

  return {
    bedtime:          minutesToTime(bedNormFinal),
    bedtimeRange: {
      early: minutesToTime(bedNormFinal - 30),
      late:  minutesToTime(bedNormFinal + 30),
    },
    targetSleepHours,
    adjustments,
  };
}
