// ─────────────────────────────────────────
// REVERIE — firebase.js
// Firebase config + Auth + Firestore helpers
// Include this script in every HTML page
// ─────────────────────────────────────────

import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.1/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.1.1/firebase-auth.js";
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
} from "https://www.gstatic.com/firebasejs/12.1.1/firebase-firestore.js";

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
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// ─────────────────────────────────────────
// AUTH HELPERS
// ─────────────────────────────────────────

// Sign up a new user with email + password
// Also saves their name + onboarding profile to Firestore
export async function signUp(name, email, password, profile = {}) {
  const cred = await createUserWithEmailAndPassword(auth, email, password);
  const uid = cred.user.uid;

  // Save profile to Firestore
  await setDoc(doc(db, "users", uid), {
    name,
    email,
    chronotype: profile.chronotype || null,
    goal: profile.goal || null,
    wakeTime: profile.wakeTime || "07:00",
    createdAt: serverTimestamp()
  });

  return cred.user;
}

// Log in existing user
export async function logIn(email, password) {
  const cred = await signInWithEmailAndPassword(auth, email, password);
  return cred.user;
}

// Log out
export async function logOut() {
  await signOut(auth);
  window.location.href = "/frontend/pages/onboarding.html";
}

// Get the currently logged in user (returns null if not logged in)
export function getCurrentUser() {
  return auth.currentUser;
}

// Listen for auth state changes — use this on every page to
// redirect to onboarding if not logged in
export function requireAuth(callback) {
  onAuthStateChanged(auth, user => {
    if (!user) {
      window.location.href = "/frontend/pages/onboarding.html";
    } else {
      callback(user);
    }
  });
}

// ─────────────────────────────────────────
// USER PROFILE HELPERS
// ─────────────────────────────────────────

// Get a user's profile from Firestore
export async function getUserProfile(uid) {
  const snap = await getDoc(doc(db, "users", uid));
  return snap.exists() ? snap.data() : null;
}

// Update a user's profile fields
export async function updateUserProfile(uid, updates) {
  await setDoc(doc(db, "users", uid), updates, { merge: true });
}

// ─────────────────────────────────────────
// DREAM HELPERS
// ─────────────────────────────────────────

// Save a new dream entry to Firestore
// dreamData should include: { text, emotions, themes, summary }
export async function saveDream(uid, dreamData) {
  const dreamsRef = collection(db, "users", uid, "dreams");
  const docRef = await addDoc(dreamsRef, {
    ...dreamData,
    createdAt: serverTimestamp()
  });
  return docRef.id;
}

// Get all dreams for a user, sorted newest first
export async function getDreams(uid) {
  const dreamsRef = collection(db, "users", uid, "dreams");
  const q = query(dreamsRef, orderBy("createdAt", "desc"));
  const snap = await getDocs(q);
  return snap.docs.map(d => ({ id: d.id, ...d.data() }));
}

// Get a single dream by ID
export async function getDream(uid, dreamId) {
  const snap = await getDoc(doc(db, "users", uid, "dreams", dreamId));
  return snap.exists() ? { id: snap.id, ...snap.data() } : null;
}

// ─────────────────────────────────────────
// SLEEP LOG HELPERS
// ─────────────────────────────────────────

// Save a sleep log entry
// logData should include: { bedtime, wakeTime, hoursSlept, date }
export async function saveSleepLog(uid, logData) {
  const logsRef = collection(db, "users", uid, "sleepLogs");
  await addDoc(logsRef, {
    ...logData,
    createdAt: serverTimestamp()
  });
}

// Get last 7 sleep logs for a user
export async function getRecentSleepLogs(uid) {
  const logsRef = collection(db, "users", uid, "sleepLogs");
  const q = query(logsRef, orderBy("createdAt", "desc"));
  const snap = await getDocs(q);
  return snap.docs.slice(0, 7).map(d => ({ id: d.id, ...d.data() }));
}

export { auth, db };