import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiCreateMood, apiGetAffirmation, apiGetTasks } from "../api/client";
import { MOOD_OPTIONS, type MoodType, type TaskItem } from "../api/types";

export default function HomePage() {
  const { user } = useAuth();
  const [affirmation, setAffirmation] = useState("");
  const [selectedMood, setSelectedMood] = useState<MoodType | null>(null);
  const [moodNote, setMoodNote] = useState("");
  const [moodSaved, setMoodSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [recentTasks, setRecentTasks] = useState<TaskItem[]>([]);

  useEffect(() => {
    apiGetAffirmation("okay").then((r) => setAffirmation(r.affirmation)).catch(() => {});
    apiGetTasks({ page: 1, page_size: 4, sort: "id_desc" }).then((r) => setRecentTasks(r.items)).catch(() => {});
  }, []);

  const handleMoodSelect = async (mood: MoodType) => {
    setSelectedMood(mood);
    setMoodSaved(false);
    try {
      const r = await apiGetAffirmation(mood);
      setAffirmation(r.affirmation);
    } catch { /* */ }
  };

  const handleMoodSubmit = async () => {
    if (!selectedMood) return;
    setSaving(true);
    const opt = MOOD_OPTIONS.find((m) => m.value === selectedMood);
    try {
      const result = await apiCreateMood(selectedMood, opt?.emoji || "😊", moodNote || undefined);
      if (result.affirmation) setAffirmation(result.affirmation);
      setMoodSaved(true);
      setMoodNote("");
    } catch { /* */ }
    setSaving(false);
  };

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "早上好" : hour < 18 ? "下午好" : "晚上好";

  return (
    <div className="home-page">
      <div className="greeting-section">
        <h1 className="greeting">
          {greeting}，{user?.username} {user?.avatar_emoji || "🌸"}
        </h1>
        <p className="greeting-sub">今天也要温柔地对待自己哦</p>
      </div>

      {affirmation && (
        <div className="affirmation-card">
          <p className="affirmation-text">{affirmation}</p>
        </div>
      )}

      <div className="mood-section">
        <h2>此刻的心情是？</h2>
        <div className="mood-picker">
          {MOOD_OPTIONS.map((m) => (
            <button
              key={m.value}
              className={`mood-btn ${selectedMood === m.value ? "active" : ""}`}
              onClick={() => handleMoodSelect(m.value)}
            >
              <span className="mood-emoji">{m.emoji}</span>
              <span className="mood-label">{m.label}</span>
            </button>
          ))}
        </div>

        {selectedMood && !moodSaved && (
          <div className="mood-note-section">
            <textarea
              className="mood-note-input"
              placeholder="想说点什么吗？（可选）"
              value={moodNote}
              onChange={(e) => setMoodNote(e.target.value)}
              rows={2}
            />
            <button className="btn btn-primary" onClick={handleMoodSubmit} disabled={saving}>
              {saving ? "记录中..." : "记录心情 💕"}
            </button>
          </div>
        )}

        {moodSaved && (
          <div className="mood-saved">
            <span>心情已记录 ✨ </span>
            <button className="btn-link" onClick={() => { setMoodSaved(false); setSelectedMood(null); }}>
              再记一次
            </button>
          </div>
        )}
      </div>

      <div className="quick-actions">
        <Link to="/transform" className="action-card">
          <span className="action-emoji">🎨</span>
          <span className="action-title">AI 变身</span>
          <span className="action-desc">把照片变成卡通风格</span>
        </Link>
        <Link to="/gallery" className="action-card">
          <span className="action-emoji">🖼️</span>
          <span className="action-title">治愈画廊</span>
          <span className="action-desc">欣赏你的作品集</span>
        </Link>
        <Link to="/profile" className="action-card">
          <span className="action-emoji">💜</span>
          <span className="action-title">心情轨迹</span>
          <span className="action-desc">回顾你的心情历程</span>
        </Link>
      </div>

      {recentTasks.length > 0 && (
        <div className="recent-section">
          <div className="section-header">
            <h2>最近的创作</h2>
            <Link to="/tasks" className="btn-link">查看全部 →</Link>
          </div>
          <div className="recent-grid">
            {recentTasks.map((t) => (
              <div key={t.task_id} className={`recent-card status-${t.status}`}>
                <div className="recent-card-top">
                  <span className="recent-style">{t.style === "warm_cartoon" ? "🧸" : "🎨"} {t.title || `#${t.task_id}`}</span>
                  <span className={`badge-sm status-${t.status}`}>
                    {t.status === "completed" ? "✅" : t.status === "processing" ? "⏳" : t.status === "queued" ? "🕐" : "❌"}
                  </span>
                </div>
                {t.status === "processing" && (
                  <div className="mini-progress"><div className="mini-progress-fill" style={{ width: `${t.progress}%` }} /></div>
                )}
                {t.status === "completed" && t.output_url && (
                  <a href={t.output_url} target="_blank" rel="noopener noreferrer" className="btn-link" style={{ fontSize: "0.8rem" }}>
                    查看作品 →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
