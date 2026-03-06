const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const handleResponse = async (response) => {
  if (!response.ok) {
    let errorMessage = `Error ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // If JSON parsing fails, use default message
    }
    throw new Error(errorMessage);
  }
  return response.json();
};

export const api = {
  // Auth
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return handleResponse(response);
  },

  async register(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return handleResponse(response);
  },

  // Sessions
  async listSessions() {
    const response = await fetch(`${API_BASE_URL}/sessions/`, {
      headers: getAuthHeader()
    });
    return handleResponse(response);
  },

  async getSessionDetail(sessionId) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      headers: getAuthHeader()
    });
    return handleResponse(response);
  },

  async createSession(title) {
    const response = await fetch(`${API_BASE_URL}/sessions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify({ title })
    });
    return handleResponse(response);
  },

  async uploadReferences(sessionId, files) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/references`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData
    });
    return handleResponse(response);
  },

  async uploadQuestionnaire(sessionId, file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/questionnaire`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData
    });
    return handleResponse(response);
  },

  async generateAnswers(sessionId) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/generate-answers`, {
      method: 'POST',
      headers: getAuthHeader()
    });
    return handleResponse(response);
  },

  async regenerateSelected(sessionId, questionIds) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify({ question_ids: questionIds })
    });
    return handleResponse(response);
  },

  async updateQuestion(questionId, answer) {
    const response = await fetch(`${API_BASE_URL}/sessions/questions/${questionId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify({ answer, is_edited: true })
    });
    return handleResponse(response);
  },

  async exportSession(sessionId) {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/export?format=docx`, {
      headers: getAuthHeader()
    });
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }
    return response.blob();
  }
};
