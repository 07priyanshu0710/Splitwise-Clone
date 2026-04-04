const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

export const setToken = (token) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', token);
  }
};

export const removeToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
  }
};

async function fetchWithAuth(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (response.status === 401) {
    removeToken();
    if (typeof window !== 'undefined' && window.location.pathname !== '/') {
      window.location.href = '/';
    }
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Unauthorized');
  }

  if (!response.ok) {
    if (Array.isArray(data.detail)) {
      throw new Error(data.detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join(', '));
    }
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail) || 'An error occurred');
  }

  return data;
}

export const api = {
  // Auth
  login: (username, password) => {
    // URLSearchParams for form-urlencoded required by OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    return fetchWithAuth('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString()
    });
  },
  register: (email, password, fullName) => 
    fetchWithAuth('/auth/register', { 
      method: 'POST', 
      body: JSON.stringify({ email, password, full_name: fullName }) 
    }),
  getMe: () => fetchWithAuth('/users/me'),

  // Balances
  getMyBalances: () => fetchWithAuth('/balances/me'),

  // Groups
  getGroups: () => fetchWithAuth('/groups/'),
  getGroup: (id) => fetchWithAuth(`/groups/${id}`),
  createGroup: (name) => fetchWithAuth('/groups/', { method: 'POST', body: JSON.stringify({ name }) }),
  addGroupMember: (groupId, email) => fetchWithAuth(`/groups/${groupId}/members`, { method: 'POST', body: JSON.stringify({ email }) }),

  // Expenses
  getGroupExpenses: (groupId) => fetchWithAuth(`/expenses/group/${groupId}`),
  createExpense: (payload) => fetchWithAuth(`/expenses/`, { method: 'POST', body: JSON.stringify(payload) }),

  // Summary
  getMonthlySummary: () => fetchWithAuth('/reports/monthly-summary'),
};
