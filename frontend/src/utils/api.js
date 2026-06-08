// src/utils/api.js
// Centralised API client for all backend requests.

const BASE_URL = "http://localhost:5000/api";

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (name, email, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) }),

  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  me: () => request("/auth/me"),
};

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const dashboardAPI = {
  get: () => request("/dashboard"),
};

// ── Interviews ─────────────────────────────────────────────────────────────────
export const interviewAPI = {
  start: (role, level, category) =>
    request("/interviews/start", {
      method: "POST",
      body: JSON.stringify({ role, level, category }),
    }),

  submitAnswer: (interviewId, questionId, answer, timeTaken) =>
    request(`/interviews/${interviewId}/answer`, {
      method: "POST",
      body: JSON.stringify({
        question_id: questionId,
        answer,
        time_taken: timeTaken,
      }),
    }),

  end: (interviewId) =>
    request(`/interviews/${interviewId}/end`, { method: "POST" }),

  getReport: (interviewId) =>
    request(`/interviews/${interviewId}/report`),
};
