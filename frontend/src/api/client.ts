import type {
  TokenResponse, UserMe, TaskListResponse, StyleInfo, MoodItem, MoodListResponse,
} from "./types";

const TOKEN_KEY = "echomie_token";

function getToken(): string | null { return localStorage.getItem(TOKEN_KEY); }
export function setToken(token: string) { localStorage.setItem(TOKEN_KEY, token); }
export function clearToken() { localStorage.removeItem(TOKEN_KEY); }
export function hasToken(): boolean { return !!localStorage.getItem(TOKEN_KEY); }

class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const b = await res.json(); detail = b.detail || JSON.stringify(b); } catch { /* */ }
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

// Auth
export const apiRegister = (username: string, email: string, password: string) =>
  request<TokenResponse>("/api/register", { method: "POST", body: JSON.stringify({ username, email, password }) });
export const apiLogin = (identifier: string, password: string) =>
  request<TokenResponse>("/api/login", { method: "POST", body: JSON.stringify({ identifier, password }) });
export const apiGetMe = () => request<UserMe>("/api/me");
export const apiUpdateAvatar = (avatar_emoji: string) =>
  request<{ ok: boolean }>("/api/me/avatar", { method: "PUT", body: JSON.stringify({ avatar_emoji }) });

// Password
export const apiForgotCode = (email: string) =>
  request<{ ok: boolean; cooldown_seconds: number }>("/api/password/forgot-code", { method: "POST", body: JSON.stringify({ email }) });
export const apiResetByCode = (email: string, code: string, new_password: string) =>
  request<{ ok: boolean }>("/api/password/reset-by-code", { method: "POST", body: JSON.stringify({ email, code, new_password }) });
export const apiChangePassword = (old_password: string, new_password: string) =>
  request<{ ok: boolean }>("/api/password/change", { method: "POST", body: JSON.stringify({ old_password, new_password }) });

// Styles
export const apiGetStyles = () => request<{ styles: StyleInfo[] }>("/api/styles");

// Upload
export async function apiUpload(file: File, style: string, title: string): Promise<{ code: number; data: Record<string, unknown> }> {
  const form = new FormData();
  form.append("file", file);
  form.append("style", style);
  form.append("title", title);
  form.append("params_json", JSON.stringify({ style }));
  return request("/api/upload", { method: "POST", body: form });
}

// Tasks
export const apiGetTasks = (p: { page?: number; page_size?: number; status?: string; style?: string; sort?: string }) => {
  const qs = new URLSearchParams();
  if (p.page) qs.set("page", String(p.page));
  if (p.page_size) qs.set("page_size", String(p.page_size));
  if (p.status) qs.set("status", p.status);
  if (p.style) qs.set("style", p.style);
  if (p.sort) qs.set("sort", p.sort);
  return request<TaskListResponse>(`/api/tasks?${qs}`);
};
export const apiGetGallery = (p: { page?: number; page_size?: number; style?: string }) => {
  const qs = new URLSearchParams();
  if (p.page) qs.set("page", String(p.page));
  if (p.page_size) qs.set("page_size", String(p.page_size));
  if (p.style) qs.set("style", p.style);
  return request<TaskListResponse>(`/api/gallery?${qs}`);
};
export const apiCancelTask = (id: number) => request<{ ok: boolean }>(`/api/tasks/${id}/cancel`, { method: "POST" });
export const apiRetryTask = (id: number) => request<{ ok: boolean }>(`/api/tasks/${id}/retry`, { method: "POST" });
export const apiDeleteTask = (id: number) => request<{ ok: boolean }>(`/api/tasks/${id}`, { method: "DELETE" });
export const apiGetDownload = (id: number) => request<{ download_url: string }>(`/api/download?task_id=${id}`);

// Mood
export const apiCreateMood = (mood: string, emoji: string, note?: string) =>
  request<MoodItem>("/api/mood", { method: "POST", body: JSON.stringify({ mood, emoji, note }) });
export const apiGetMoods = (limit = 30) => request<MoodListResponse>(`/api/moods?limit=${limit}`);
export const apiGetAffirmation = (mood = "okay") => request<{ affirmation: string }>(`/api/affirmation?mood=${mood}`);

export { ApiError };
