// ─────────────────────────────────────────
// sleepEngine.test.js
// Browser-native ES module test suite.
//
// Run from browser console:
//   import('/frontend/tests/sleepEngine.test.js')
//
// Or open tests/runner.html in a browser.
// ─────────────────────────────────────────

import {
  calculateBedtime,
  timeToMinutes,
  minutesToTime,
  formatTime12h,
  ageToSleepHours,
  applyDefaults,
} from "../js/sleepEngine.js";

// ── Tiny test harness ─────────────────────

let passed = 0;
let failed = 0;

function assert(label, condition) {
  if (condition) {
    console.log(`  ✅  ${label}`);
    passed++;
  } else {
    console.error(`  ❌  ${label}`);
    failed++;
  }
}

function eq(label, actual, expected) {
  const ok = actual === expected;
  if (!ok) console.error(`       got "${actual}", expected "${expected}"`);
  assert(label, ok);
}

function suite(name, fn) {
  console.groupCollapsed(`▶ ${name}`);
  fn();
  console.groupEnd();
}

// ── Helper tests ──────────────────────────

suite("timeToMinutes", () => {
  eq("07:00 → 420",  timeToMinutes("07:00"), 420);
  eq("00:00 → 0",    timeToMinutes("00:00"), 0);
  eq("23:30 → 1410", timeToMinutes("23:30"), 1410);
  assert("null input returns null", timeToMinutes(null) === null);
  assert("bad string returns null", timeToMinutes("abc") === null);
});

suite("minutesToTime", () => {
  eq("420 → 07:00",   minutesToTime(420),  "07:00");
  eq("-60 → 23:00",   minutesToTime(-60),  "23:00");
  eq("1440 → 00:00",  minutesToTime(1440), "00:00");
  eq("1500 → 01:00",  minutesToTime(1500), "01:00");
});

suite("formatTime12h", () => {
  eq("23:00 → 11:00 PM", formatTime12h("23:00"), "11:00 PM");
  eq("07:30 → 7:30 AM",  formatTime12h("07:30"), "7:30 AM");
  eq("12:00 → 12:00 PM", formatTime12h("12:00"), "12:00 PM");
  eq("00:00 → 12:00 AM", formatTime12h("00:00"), "12:00 AM");
});

suite("ageToSleepHours", () => {
  assert("age 15 → 9h",   ageToSleepHours(15)  === 9);
  assert("age 20 → 8.5h", ageToSleepHours(20)  === 8.5);
  assert("age 40 → 8h",   ageToSleepHours(40)  === 8);
  assert("age 70 → 7.5h", ageToSleepHours(70)  === 7.5);
  assert("null → 8h",     ageToSleepHours(null) === 8);
});

suite("applyDefaults", () => {
  const d = applyDefaults({});
  assert("missing wakeTime defaults to 07:00", d.wakeTime === "07:00");
  assert("missing chronotype defaults to middle", d.chronotype === "middle");
  const override = applyDefaults({ wakeTime: "06:00" });
  eq("provided wakeTime is kept", override.wakeTime, "06:00");
});

// ── calculateBedtime — core cases ─────────

suite("desiredSleepHours overrides age", () => {
  // Age 20 → 8.5 h, but desiredSleepHours: 7 should win
  const r = calculateBedtime({ wakeTime: "07:00", age: 20, desiredSleepHours: 7 });
  assert("targetSleepHours is 7, not 8.5", r.targetSleepHours === 7);
  eq("bedtime is 00:00 (420 - 420 = 0)", r.bedtime, "00:00");
});

suite("age as fallback when desiredSleepHours absent", () => {
  const r = calculateBedtime({ wakeTime: "07:00", age: 20 });
  assert("targetSleepHours is 8.5 from age", r.targetSleepHours === 8.5);
  eq("bedtime is 22:30 (420 - 510 = -90 → 22:30)", r.bedtime, "22:30");
});

suite("wake time drives the bedtime", () => {
  const r1 = calculateBedtime({ wakeTime: "06:00", desiredSleepHours: 8 });
  eq("wake 06:00 → bedtime 22:00", r1.bedtime, "22:00");

  const r2 = calculateBedtime({ wakeTime: "09:00", desiredSleepHours: 8 });
  eq("wake 09:00 → bedtime 01:00", r2.bedtime, "01:00");
});

suite("missing profile falls back gracefully", () => {
  const r = calculateBedtime({});
  assert("returns a bedtime string", typeof r.bedtime === "string");
  assert("returns targetSleepHours", typeof r.targetSleepHours === "number");
  assert("defaults to 8 h sleep (no age, no desired)", r.targetSleepHours === 8);
  assert("bedtimeRange has early and late", r.bedtimeRange.early && r.bedtimeRange.late);
});

suite("chronotype adjustments", () => {
  const base  = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, chronotype: "middle" });
  const night = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, chronotype: "night" });
  const early = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, chronotype: "early" });

  assert("night owl is 30 min later than middle",
    timeToMinutes(night.bedtime) - timeToMinutes(base.bedtime) === 30);
  assert("early bird is 30 min earlier than middle",
    timeToMinutes(base.bedtime) - timeToMinutes(early.bedtime) === 30);
  assert("night adjustment is recorded", night.adjustments.some(a => a.factor === "Chronotype"));
});

suite("caffeine pushes bedtime later", () => {
  // Base: wake 07:00, 8h sleep → bedtime 23:00 (1380 min).
  // Caffeine at 17:30 → clears at 23:30 (1410). Should push by 30 min.
  const r = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, caffeineLastCup: "17:30" });
  assert("bedtime is at least 23:30", timeToMinutes(r.bedtime) >= 1410);
  assert("caffeine adjustment is recorded", r.adjustments.some(a => a.factor === "Caffeine"));
});

suite("no caffeine push when coffee clears before bedtime", () => {
  // Coffee at 08:00, clears by 14:00. Bedtime 23:00 — no adjustment expected.
  const r = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, caffeineLastCup: "08:00" });
  assert("no caffeine adjustment", !r.adjustments.some(a => a.factor === "Caffeine"));
  eq("bedtime unchanged at 23:00", r.bedtime, "23:00");
});

suite("stress pulls bedtime earlier", () => {
  const low    = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, stressLevel: 2 });
  const high   = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, stressLevel: 5 });
  assert("high stress is 20 min earlier than low stress",
    timeToMinutes(low.bedtime) - timeToMinutes(high.bedtime) === 20);
  assert("stress adjustment recorded", high.adjustments.some(a => a.factor === "Stress"));
  assert("low stress has no adjustment",  !low.adjustments.some(a => a.factor === "Stress"));
});

suite("evening exercise pushes bedtime later", () => {
  const none    = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, exerciseTiming: "none" });
  const evening = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, exerciseTiming: "evening" });
  assert("evening exercise shifts 30 min later",
    timeToMinutes(evening.bedtime) - timeToMinutes(none.bedtime) === 30);
});

suite("long nap pushes bedtime later", () => {
  const no     = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, napsDaily: false });
  const long   = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, napsDaily: true, napDuration: 60 });
  const short  = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8, napsDaily: true, napDuration: 20 });
  assert("long nap shifts 20 min later",  timeToMinutes(long.bedtime)  - timeToMinutes(no.bedtime) === 20);
  assert("short nap has no adjustment",   timeToMinutes(short.bedtime) === timeToMinutes(no.bedtime));
});

suite("combined factors accumulate correctly", () => {
  // night owl (+30) + evening exercise (+30) + high stress (-20) = net +40 vs middle/no-exercise/low-stress
  const base = calculateBedtime({ wakeTime: "07:00", desiredSleepHours: 8 });
  const full = calculateBedtime({
    wakeTime: "07:00", desiredSleepHours: 8,
    chronotype: "night", exerciseTiming: "evening", stressLevel: 5,
  });
  const diff = timeToMinutes(full.bedtime) - timeToMinutes(base.bedtime);
  assert("combined adjustments net +40 min", diff === 40);
});

// ── Summary ───────────────────────────────

console.log("");
console.log(`Results: ${passed} passed, ${failed} failed`);
if (failed === 0) console.log("All tests passed ✅");
