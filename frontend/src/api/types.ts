export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserMe {
  id: number;
  username: string;
  email: string;
  avatar_emoji: string;
  created_at: string;
}

export interface StyleInfo {
  key: string;
  label: string;
  emoji: string;
  desc: string;
}

export interface TaskItem {
  task_id: number;
  user_id: number;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  style: string;
  title: string | null;
  params: Record<string, unknown>;
  error_msg: string | null;
  input_url: string | null;
  output_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskListResponse {
  items: TaskItem[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
  self_url: string;
  next_url: string | null;
  prev_url: string | null;
}

export interface MoodItem {
  id: number;
  mood: string;
  emoji: string;
  note: string | null;
  affirmation: string | null;
  created_at: string;
}

export interface MoodListResponse {
  items: MoodItem[];
  total: number;
}

export type MoodType = "great" | "good" | "okay" | "sad" | "anxious";

export const MOOD_OPTIONS: { value: MoodType; emoji: string; label: string }[] = [
  { value: "great", emoji: "🥳", label: "超开心" },
  { value: "good", emoji: "😊", label: "还不错" },
  { value: "okay", emoji: "😐", label: "一般般" },
  { value: "sad", emoji: "😢", label: "有点丧" },
  { value: "anxious", emoji: "😰", label: "很焦虑" },
];
