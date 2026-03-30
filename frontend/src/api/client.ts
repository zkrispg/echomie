import type {
  TokenResponse, UserMe, TaskItem, TaskStatusResponse,
  TaskListResponse, MoodItem, MoodListResponse,
  WeeklySummaryListResponse, StyleListResponse,
} from "./types";

const TOKEN_KEY = "echomie_token";

export function setToken(t: string) { localStorage.setItem(TOKEN_KEY, t); }
export function clearToken() { localStorage.removeItem(TOKEN_KEY); }
export function hasToken() { return !!localStorage.getItem(TOKEN_KEY); }

export class ApiError extends Error {
  status: number;
  constructor(msg: string, status: number) { super(msg); this.status = status; }
}

async function request<T>(url: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(url, { ...opts, headers: { ...headers, ...(opts.headers as Record<string, string> || {}) } });
  if (!res.ok) {
    let msg = res.statusText;
    try { const j = await res.json(); msg = j.detail || msg; } catch {}
    throw new ApiError(msg, res.status);
  }
  return res.json();
}

// Auth
export const apiRegister = (d: { username: string; email: string; password: string }) =>
  request<TokenResponse>("/api/register", { method: "POST", body: JSON.stringify(d) });

export const apiLogin = (d: { identifier: string; password: string }) =>
  request<TokenResponse>("/api/login", { method: "POST", body: JSON.stringify(d) });

export const apiGetMe = () => request<UserMe>("/api/me");

export const apiUpdateAvatar = (emoji: string) =>
  request<{ ok: boolean }>("/api/me/avatar", { method: "PUT", body: JSON.stringify({ avatar_emoji: emoji }) });

// Password
export const apiForgotCode = (email: string) =>
  request<{ ok: boolean; cooldown_seconds: number }>("/api/password/forgot-code", { method: "POST", body: JSON.stringify({ email }) });

export const apiResetByCode = (d: { email: string; code: string; new_password: string }) =>
  request<{ ok: boolean }>("/api/password/reset-by-code", { method: "POST", body: JSON.stringify(d) });

export const apiChangePassword = (d: { old_password: string; new_password: string }) =>
  request<{ ok: boolean }>("/api/password/change", { method: "POST", body: JSON.stringify(d) });

// Styles
export const apiGetStyles = () =>
  request<StyleListResponse>("/api/styles");

// Upload (emotion record + optional cartoon style)
export const apiUpload = (file: File, context: string = "", style: string = "none") => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("context", context);
  fd.append("style", style);
  return request<{ code: number; data: { task_id: number } }>("/api/upload", { method: "POST", body: fd });
};

// Tasks
export const apiGetStatus = (taskId: number) =>
  request<TaskStatusResponse>(`/api/status?task_id=${taskId}`);

export const apiGetTasks = (p: { page?: number; page_size?: number; status?: string; sort?: string } = {}) => {
  const q = new URLSearchParams();
  if (p.page) q.set("page", String(p.page));
  if (p.page_size) q.set("page_size", String(p.page_size));
  if (p.status) q.set("status", p.status);
  if (p.sort) q.set("sort", p.sort);
  return request<TaskListResponse>(`/api/tasks?${q}`);
};

export const apiGetTimeline = (p: { page?: number; page_size?: number } = {}) => {
  const q = new URLSearchParams();
  if (p.page) q.set("page", String(p.page));
  if (p.page_size) q.set("page_size", String(p.page_size));
  return request<TaskListResponse>(`/api/timeline?${q}`);
};

export const apiCancelTask = (id: number) =>
  request<{ ok: boolean }>(`/api/tasks/${id}/cancel`, { method: "POST" });

export const apiRetryTask = (id: number) =>
  request<{ ok: boolean }>(`/api/tasks/${id}/retry`, { method: "POST" });

export const apiDeleteTask = (id: number) =>
  request<{ ok: boolean }>(`/api/tasks/${id}`, { method: "DELETE" });

// Mood
export const apiCreateMood = (d: { mood: string; emoji: string; note?: string }) =>
  request<MoodItem>("/api/mood", { method: "POST", body: JSON.stringify(d) });

export const apiGetMoods = (limit: number = 30) =>
  request<MoodListResponse>(`/api/moods?limit=${limit}`);

export const apiGetAffirmation = (mood: string = "okay") =>
  request<{ affirmation: string; mood: string }>(`/api/affirmation?mood=${mood}`);

// Weekly Summary
export const apiGetWeeklySummaries = (limit: number = 10) =>
  request<WeeklySummaryListResponse>(`/api/weekly-summary?limit=${limit}`);

export const apiGenerateWeeklySummary = () =>
  request<{ ok: boolean; summary_id: number }>("/api/weekly-summary/generate", { method: "POST" });
