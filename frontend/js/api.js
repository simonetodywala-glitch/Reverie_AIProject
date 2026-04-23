// ─────────────────────────────────────────
// REVERIE — api.js
// All fetch calls to the FastAPI backend
// ─────────────────────────────────────────

const BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : 'https://reverie-aiproject.onrender.com';

// ── DREAMS ──

// Save a new dream entry (text) → returns AI analysis
async function analyzeDream(dreamText) {
  let res;
  try {
    res = await fetch(`${BASE_URL}/dreams/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: dreamText })
    });
  } catch {
    throw new Error('Cannot reach the Reverie backend. Make sure it is running: uvicorn backend.main:app --reload');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Backend error ${res.status}`);
  }
  return res.json();
}

// Get all saved dream entries for the current user
async function getDreams(userId) {
  const res = await fetch(`${BASE_URL}/dreams/${userId}`);
  if (!res.ok) throw new Error('Failed to fetch dreams');
  return res.json();
}

// ── INSIGHTS ──

// Send a chat message to the AI chatbot (with user's dream history as context)
async function sendChatMessage(userId, message) {
  const res = await fetch(`${BASE_URL}/analysis/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message })
  });
  if (!res.ok) throw new Error('Chat failed');
  return res.json(); // { reply }
}

// Get dream pattern report (requires 5+ dreams)
async function getPatternReport(userId) {
  const res = await fetch(`${BASE_URL}/analysis/patterns/${userId}`);
  if (!res.ok) throw new Error('Failed to get pattern report');
  return res.json();
}

// ── SLEEP SCHEDULE ──

// Generate a personalised Gemini tip from the full sleep profile + result
async function getSleepTip(profile, result) {
  const res = await fetch(`${BASE_URL}/schedule/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      wake_time:        profile.wakeTime,
      bedtime:          result.bedtime,
      target_hours:     result.targetSleepHours,
      age:              profile.age              || null,
      caffeine_last_cup: profile.caffeineLastCup || null,
      last_meal_time:   profile.lastMealTime     || null,
      exercise_timing:  profile.exerciseTiming   || 'none',
      stress_level:     profile.stressLevel      || 2,
      alcohol_nightly:  profile.alcoholNightly   || false,
      shift_work:       profile.shiftWork        || false,
      chronotype:       profile.chronotype       || null,
      adjustments:      (result.adjustments || []).map(a => a.note),
    })
  });
  if (!res.ok) throw new Error('Tip generation failed');
  return res.json(); // { tip }
}

// ── AUDIO ──

// Generate a bedtime story from dream text (returns audio URL)
async function generateBedtimeStory(dreamText) {
  const res = await fetch(`${BASE_URL}/audio/story`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dream_text: dreamText })
  });
  if (!res.ok) throw new Error('Story generation failed');
  return res.json(); // { audio_url }
}

// Get a soundscape audio URL by mood
async function getSoundscape(mood) {
  const res = await fetch(`${BASE_URL}/audio/soundscape/${mood}`);
  if (!res.ok) throw new Error('Soundscape failed');
  return res.json(); // { audio_url }
}
