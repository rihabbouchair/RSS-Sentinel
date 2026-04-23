const API_BASE = '/api';

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

async function parseJson(response, fallbackMessage) {
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || data?.message || fallbackMessage);
  }

  return data;
}

export async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  return parseJson(response, 'Login failed');
}

export async function register({ username, password, email, topics, wants_email_digest }) {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, email, topics, wants_email_digest }),
  });
  return parseJson(response, 'Registration failed');
}

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch user');
}

export async function getArticles({ feedTopic, sentiment, limit = 20 } = {}) {
  const params = new URLSearchParams();
  if (feedTopic) params.append('feed_topic', feedTopic);
  if (sentiment) params.append('sentiment', sentiment);
  params.append('limit', limit);

  const response = await fetch(`${API_BASE}/articles?${params.toString()}`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch articles');
}

export async function getTopics() {
  const response = await fetch(`${API_BASE}/articles/topics`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch topics');
}

export async function getFeeds() {
  const response = await fetch(`${API_BASE}/feeds`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch feeds');
}

export async function updatePreferences({ topics, email, wants_email_digest }) {
  const response = await fetch(`${API_BASE}/users/preferences`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ topics, email, wants_email_digest }),
  });
  return parseJson(response, 'Failed to update preferences');
}

export async function requestEmailVerification() {
  const response = await fetch(`${API_BASE}/users/email/request-verification`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to send verification code');
}

export async function verifyEmailCode(code) {
  const response = await fetch(`${API_BASE}/users/email/verify`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ code }),
  });
  return parseJson(response, 'Failed to verify email');
}
