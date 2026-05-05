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

export async function register({ username, password, topics, wants_email_digest, language_preferences }) {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, topics, wants_email_digest, language_preferences }),
  });
  return parseJson(response, 'Registration failed');
}

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch user');
}

export async function getArticles({ feedTopic, sentiment, limit = 20, showRead = false } = {}) {
  const params = new URLSearchParams();
  if (feedTopic) params.append('feed_topic', feedTopic);
  if (sentiment) params.append('sentiment', sentiment);
  params.append('limit', limit);
  params.append('show_read', showRead);

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

export async function getTopicCounts() {
  const response = await fetch(`${API_BASE}/articles/topic-counts`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch topic counts');
}

export async function getFeeds() {
  const response = await fetch(`${API_BASE}/feeds`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch feeds');
}

export async function updatePreferences({ topics, email, wants_email_digest, language_preferences, articles_per_topic }) {
  const response = await fetch(`${API_BASE}/users/preferences`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ topics, email, wants_email_digest, language_preferences, articles_per_topic }),
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

export async function refreshArticles() {
  const response = await fetch(`${API_BASE}/articles/refresh`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to refresh articles');
}

export async function refreshTopic(topic) {
  const params = new URLSearchParams();
  if (topic) params.append('topic', topic);
  const response = await fetch(`${API_BASE}/articles/refresh-topic?${params.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to refresh topic');
}

// ── Read/Unread Tracking ──────────────────────────────────────────────────────
export async function markArticleRead(articleId) {
  const response = await fetch(`${API_BASE}/articles/${articleId}/mark-read`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to mark article as read');
}

export async function markArticleUnread(articleId) {
  const response = await fetch(`${API_BASE}/articles/${articleId}/mark-unread`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to mark article as unread');
}

export async function markAllArticlesRead(topic = null) {
  const params = new URLSearchParams();
  if (topic) params.append('topic', topic);
  const response = await fetch(`${API_BASE}/articles/mark-all-read?${params.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to mark articles as read');
}

export async function getUnreadCounts() {
  const response = await fetch(`${API_BASE}/articles/unread-counts`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch unread counts');
}

// ── Feed Discovery & Recommendations ───────────────────────────────────────────
export async function discoverFeeds(topicOrTopics = null, limit = 10) {
  const params = new URLSearchParams();
  if (Array.isArray(topicOrTopics)) {
    topicOrTopics.filter(Boolean).forEach((topic) => params.append('topics', topic));
  } else if (topicOrTopics) {
    params.append('topic', topicOrTopics);
  }
  params.append('limit', limit);
  const response = await fetch(`${API_BASE}/feeds/discover?${params.toString()}`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch feeds');
}

export async function discoverFeedTopics() {
  const response = await fetch(`${API_BASE}/feeds/discover/topics`, {
    headers: getAuthHeaders(),
  });
  return parseJson(response, 'Failed to fetch topics');
}

export async function subscribeToFeed(feedId) {
  const response = await fetch(`${API_BASE}/feeds/subscribe`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ feed_id: feedId }),
  });
  return parseJson(response, 'Failed to subscribe to feed');
}
