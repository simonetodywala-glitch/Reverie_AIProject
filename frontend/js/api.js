// ─────────────────────────────────────────
// REVERIE — api.js
// All fetch calls to the FastAPI backend
// ─────────────────────────────────────────

const BASE_URL = 'http://127.0.0.1:8000';

// ── DREAMS ──

// Save a new dream entry (text) → returns AI analysis
async function analyzeDream(dreamText) {
  const res = await fetch(`${BASE_URL}/dreams/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: dreamText })
  });
  if (!res.ok) throw new Error('Failed to analyze dream');
  return res.json(); // { emotions, themes, summary }
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

// Calculate optimal bedtime from age + wake time
async function getSleepSchedule(age, wakeTime) {
  const res = await fetch(`${BASE_URL}/schedule/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ age, wake_time: wakeTime })
  });
  if (!res.ok) throw new Error('Schedule calculation failed');
  return res.json(); // { bedtime, recommended_hours, tip }
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
