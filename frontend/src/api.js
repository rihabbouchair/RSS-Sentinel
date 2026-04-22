const API_BASE = '/api';

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
}

export async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }
  return response.json();
}

export async function register({ username, password, email, topics, wants_email_digest }) {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, email, topics, wants_email_digest }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }
  return response.json();
}

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error('Failed to fetch user');
  return response.json();
}

export async function getArticles({ category, sentiment, limit = 20 } = {}) {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (sentiment) params.append('sentiment', sentiment);
  params.append('limit', limit);
  const res = await fetch(`/api/articles?${params}`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error('Failed to fetch articles');
  return res.json();
}

export async function getTopics() {
  const response = await fetch(`${API_BASE}/articles/topics`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error('Failed to fetch topics');
  return response.json();
}

export async function getFeeds() {
  const response = await fetch(`${API_BASE}/feeds`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error('Failed to fetch feeds');
  return response.json();
}

export async function updatePreferences({ topics, email, wants_email_digest }) {
  const response = await fetch(`${API_BASE}/users/preferences`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ topics, email, wants_email_digest }),
  });
  if (!response.ok) throw new Error('Failed to update preferences');
  return response.json();
}
