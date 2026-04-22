// ─────────────────────────────────────────
// REVERIE — firebase.js
// Firebase config + Firestore database helpers
// ─────────────────────────────────────────

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getFirestore,
  doc,
  setDoc,
  getDoc,
  addDoc,
  getDocs,
  collection,
  query,
  orderBy,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

// ── CONFIG ──
const firebaseConfig = {
  apiKey: "AIzaSyDfz7_RNNfjqIvkwA7faYDFMedBisaYDAY",
  authDomain: "reverie-ai-caa66.firebaseapp.com",
  projectId: "reverie-ai-caa66",
  storageBucket: "reverie-ai-caa66.firebasestorage.app",
  messagingSenderId: "311270900598",
  appId: "1:311270900598:web:8390c79ac8ea411b78b057",
  measurementId: "G-BNJ6ZQ5EB9"
};

// ── INIT ──
export const app = initializeApp(firebaseConfig);
export const db  = getFirestore(app);

// ─────────────────────────────────────────
// USER PROFILE
// ─────────────────────────────────────────

export async function saveUserProfile(uid, data) {
  await setDoc(doc(db, "users", uid), data, { merge: true });
}

export async function getUserProfile(uid) {
  const snap = await getDoc(doc(db, "users", uid));
  return snap.exists() ? snap.data() : null;
}

// ─────────────────────────────────────────
// DREAMS
// ─────────────────────────────────────────

// dreamData: { text, emotions, themes, summary }
export async function saveDream(uid, dreamData) {
  const ref = collection(db, "users", uid, "dreams");
  const docRef = await addDoc(ref, {
    ...dreamData,
    createdAt: serverTimestamp()
  });
  return docRef.id;
}

export async function getDreams(uid) {
  const ref  = collection(db, "users", uid, "dreams");
  const q    = query(ref, orderBy("createdAt", "desc"));
  const snap = await getDocs(q);
  return snap.docs.map(d => ({ id: d.id, ...d.data() }));
}

export async function getDream(uid, dreamId) {
  const snap = await getDoc(doc(db, "users", uid, "dreams", dreamId));
  return snap.exists() ? { id: snap.id, ...snap.data() } : null;
}

// ─────────────────────────────────────────
// SLEEP LOGS
// ─────────────────────────────────────────

// logData: { bedtime, wakeTime, hoursSlept, date }
export async function saveSleepLog(uid, logData) {
  const ref = collection(db, "users", uid, "sleepLogs");
  await addDoc(ref, { ...logData, createdAt: serverTimestamp() });
}

export async function getRecentSleepLogs(uid) {
  const ref  = collection(db, "users", uid, "sleepLogs");
  const q    = query(ref, orderBy("createdAt", "desc"));
  const snap = await getDocs(q);
  return snap.docs.slice(0, 7).map(d => ({ id: d.id, ...d.data() }));
}