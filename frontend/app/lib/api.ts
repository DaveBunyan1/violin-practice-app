const API_BASE = `http://${process.env.NEXT_PUBLIC_WEBSOCKET_HOST || "localhost"}:${process.env.NEXT_PUBLIC_WEBSOCKET_PORT || "8000"}`;

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "API request failed");
  }

  return res.json();
}

export const api = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, body?: unknown) =>
    request<T>(url, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(url: string, body?: unknown) =>
    request<T>(url, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),
  del: <T>(url: string) =>
    request<T>(url, {
      method: "DELETE",
    }),
};
