function resolveApiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (configured && configured.trim()) {
    return configured.trim();
  }

  // Vite local dev server typically runs on :3000 and calls backend :8000.
  if (typeof window !== "undefined" && window.location.port === "3000") {
    return "http://localhost:8000";
  }

  // Docker/Nginx and production deployments should use same-origin /api proxy.
  return "";
}

const API_BASE_URL = resolveApiBaseUrl();

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export async function apiFetch(path, options = {}) {
  const response = await fetch(apiUrl(path), options);
  return response;
}
