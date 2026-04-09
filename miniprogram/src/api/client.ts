import Taro from "@tarojs/taro";
import type {
  TokenResponse, UserMe, TaskItem, TaskStatusResponse,
  TaskListResponse, MoodItem, MoodListResponse,
  WeeklySummaryListResponse, StyleListResponse,
} from "./types";

const TOKEN_KEY = "echomie_token";

// 上线前改为 HTTPS 域名；开发阶段可在微信开发者工具中关闭域名校验
const BASE_URL = "http://47.99.54.112";

export function setToken(t: string) { Taro.setStorageSync(TOKEN_KEY, t); }
export function clearToken() { Taro.removeStorageSync(TOKEN_KEY); }
export function getToken(): string { return Taro.getStorageSync(TOKEN_KEY) || ""; }
export function hasToken() { return !!getToken(); }

export class ApiError extends Error {
  status: number;
  constructor(msg: string, status: number) { super(msg); this.status = status; }
}

async function request<T>(url: string, opts: { method?: keyof Taro.request.Method; data?: any; header?: Record<string, string> } = {}): Promise<T> {
  const header: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) header["Authorization"] = `Bearer ${token}`;
  if (opts.header) Object.assign(header, opts.header);

  const res = await Taro.request({
    url: `${BASE_URL}${url}`,
    method: (opts.method || "GET") as any,
    data: opts.data,
    header,
  });

  if (res.statusCode < 200 || res.statusCode >= 300) {
    const msg = res.data?.detail || res.errMsg || `HTTP ${res.statusCode}`;
    throw new ApiError(msg, res.statusCode);
  }
  return res.data as T;
}

// Auth - WeChat login
export const apiWxLogin = (code: string) =>
  request<TokenResponse>("/api/wx-login", { method: "POST", data: { code } });

export const apiGetMe = () => request<UserMe>("/api/me");

export const apiUpdateAvatar = (emoji: string) =>
  request<{ ok: boolean }>("/api/me/avatar", { method: "PUT", data: { avatar_emoji: emoji } });

// Styles
export const apiGetStyles = () => request<StyleListResponse>("/api/styles");

// Upload via Taro.uploadFile (FormData not available in mini programs)
export function apiUpload(filePath: string, context: string = "", style: string = "none"): Promise<{ code: number; data: { task_id: number } }> {
  return new Promise((resolve, reject) => {
    Taro.uploadFile({
      url: `${BASE_URL}/api/upload`,
      filePath,
      name: "file",
      formData: { context, style },
      header: { Authorization: `Bearer ${getToken()}` },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data));
        } else {
          let msg = `HTTP ${res.statusCode}`;
          try { msg = JSON.parse(res.data).detail || msg; } catch {}
          reject(new ApiError(msg, res.statusCode));
        }
      },
      fail(err) { reject(new ApiError(err.errMsg || "上传失败", 0)); },
    });
  });
}

// Tasks
export const apiGetStatus = (taskId: number) =>
  request<TaskStatusResponse>(`/api/status?task_id=${taskId}`);

export const apiGetTimeline = (p: { page?: number; page_size?: number } = {}) => {
  const q = new URLSearchParams();
  if (p.page) q.set("page", String(p.page));
  if (p.page_size) q.set("page_size", String(p.page_size));
  const qs = q.toString();
  return request<TaskListResponse>(`/api/timeline${qs ? `?${qs}` : ""}`);
};

// Mood
export const apiCreateMood = (d: { mood: string; emoji: string; note?: string }) =>
  request<MoodItem>("/api/mood", { method: "POST", data: d });

export const apiGetMoods = (limit: number = 30) =>
  request<MoodListResponse>(`/api/moods?limit=${limit}`);

export const apiGetAffirmation = (mood: string = "okay") =>
  request<{ affirmation: string; mood: string }>(`/api/affirmation?mood=${mood}`);

// Weekly Summary
export const apiGetWeeklySummaries = (limit: number = 10) =>
  request<WeeklySummaryListResponse>(`/api/weekly-summary?limit=${limit}`);

export const apiGenerateWeeklySummary = () =>
  request<{ ok: boolean; summary_id: number }>("/api/weekly-summary/generate", { method: "POST" });

// Password
export const apiChangePassword = (d: { old_password: string; new_password: string }) =>
  request<{ ok: boolean }>("/api/password/change", { method: "POST", data: d });

// Chat
export const apiChat = (message: string) =>
  request<{ reply: string }>("/api/chat", { method: "POST", data: { message } });

export const apiGetChatHistory = () =>
  request<{ items: { role: string; content: string; created_at: string }[] }>("/api/chat/history?limit=50");

export const apiClearChatHistory = () =>
  request<{ ok: boolean }>("/api/chat/history", { method: "DELETE" });

// Music
export const apiGetMusic = (emotion: string = "") =>
  request<{ items: import("./types").MusicItem[]; total: number }>(`/api/music?emotion=${encodeURIComponent(emotion)}`);

// Poster
export const apiGeneratePoster = (taskId: number) =>
  request<{ ok: boolean; poster_url: string }>(`/api/tasks/${taskId}/poster`);
