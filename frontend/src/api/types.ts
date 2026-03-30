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
  style?: string;
  error_msg?: string;
  user_context?: string;
  scene_description?: string;
  emotion?: string;
  emotion_emoji?: string;
  generated_title?: string;
  generated_text?: string;
  tags: string[];
  voice_url?: string;
  input_url?: string;
  output_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TaskStatusResponse extends Omit<TaskItem, "user_id"> {}

export interface StyleListResponse {
  styles: StyleInfo[];
}

export interface TaskListResponse {
  items: TaskItem[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
  self_url: string;
  next_url?: string;
  prev_url?: string;
}

export interface MoodItem {
  id: number;
  mood: string;
  emoji: string;
  note?: string;
  affirmation?: string;
  created_at: string;
}

export interface MoodListResponse {
  items: MoodItem[];
  total: number;
}

export interface WeeklySummaryItem {
  id: number;
  week_start: string;
  week_end: string;
  summary_text?: string;
  mood_trend?: string;
  tags: string[];
  encouragement?: string;
  created_at: string;
}

export interface WeeklySummaryListResponse {
  items: WeeklySummaryItem[];
  total: number;
}

export type MoodType = "great" | "good" | "okay" | "sad" | "anxious";

export const MOOD_OPTIONS: { mood: MoodType; emoji: string; label: string }[] = [
  { mood: "great", emoji: "😄", label: "超棒" },
  { mood: "good", emoji: "😊", label: "不错" },
  { mood: "okay", emoji: "😐", label: "一般" },
  { mood: "sad", emoji: "😢", label: "难过" },
  { mood: "anxious", emoji: "😰", label: "焦虑" },
];

export const EMOTION_MAP: Record<string, { label: string; emoji: string; color: string }> = {
  happy: { label: "开心", emoji: "😊", color: "#FFD93D" },
  calm: { label: "平静", emoji: "😌", color: "#A8D8EA" },
  sad: { label: "难过", emoji: "😢", color: "#B0C4DE" },
  lonely: { label: "孤独", emoji: "🥺", color: "#DDA0DD" },
  tired: { label: "疲惫", emoji: "😴", color: "#D3D3D3" },
  anxious: { label: "焦虑", emoji: "😰", color: "#FFB347" },
  hopeful: { label: "期待", emoji: "✨", color: "#98FB98" },
  nostalgic: { label: "怀念", emoji: "🌅", color: "#F4A460" },
  peaceful: { label: "安宁", emoji: "🍃", color: "#90EE90" },
  excited: { label: "兴奋", emoji: "🎉", color: "#FF69B4" },
};
