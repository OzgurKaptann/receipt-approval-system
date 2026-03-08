const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const fetchApi = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    let errorMessage = "API isteği başarısız oldu.";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // JSON parse error means non-JSON error response
    }
    throw new Error(errorMessage);
  }
  
  return response.json();
};