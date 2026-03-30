import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  apiCreateMood, apiGetMoods, apiGetAffirmation, apiGetTimeline,
} from "../api/client";
import type { MoodItem, TaskItem } from "../api/types";
import { MOOD_OPTIONS, EMOTION_MAP } from "../api/types";

export default function HomePage() {
  const { user } = useAuth();
  const [affirmation, setAffirmation] = useState("");
  const [selectedMood, setSelectedMood] = useState("");
  const [recentMoods, setRecentMoods] = useState<MoodItem[]>([]);
  const [recentCards, setRecentCards] = useState<TaskItem[]>([]);

  useEffect(() => {
    apiGetAffirmation("okay").then((r) => setAffirmation(r.affirmation)).catch(() => {});
    apiGetMoods(5).then((r) => setRecentMoods(r.items)).catch(() => {});
    apiGetTimeline({ page: 1, page_size: 3 }).then((r) => setRecentCards(r.items)).catch(() => {});
  }, []);

  const handleMood = async (mood: string, emoji: string) => {
    try {
      const r = await apiCreateMood({ mood, emoji });
      setSelectedMood(mood);
      if (r.affirmation) setAffirmation(r.affirmation);
      apiGetMoods(5).then((res) => setRecentMoods(res.items)).catch(() => {});
    } catch {}
  };

  return (
    <div className="home-page">
      <section className="home-greeting">
        <h1>
          {user?.avatar_emoji || "🌸"} 你好，{user?.username}
        </h1>
        <p className="home-affirmation">{affirmation}</p>
      </section>

      <section className="home-section">
        <h2>今日心情打卡</h2>
        <div className="mood-grid">
          {MOOD_OPTIONS.map((opt) => (
            <button
              key={opt.mood}
              className={`mood-btn${selectedMood === opt.mood ? " active" : ""}`}
              onClick={() => handleMood(opt.mood, opt.emoji)}
            >
              <span className="mood-emoji">{opt.emoji}</span>
              <span className="mood-label">{opt.label}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="home-section">
        <div className="section-header">
          <h2>最近情绪记录</h2>
          <Link to="/timeline" className="section-link">查看全部</Link>
        </div>
        {recentCards.length === 0 ? (
          <div className="empty-hint">
            <p>还没有记录</p>
            <Link to="/record" className="btn btn-primary btn-sm">记录此刻</Link>
          </div>
        ) : (
          <div className="recent-cards-grid">
            {recentCards.map((card) => {
              const em = EMOTION_MAP[card.emotion || ""] || null;
              return (
                <Link to={`/card/${card.task_id}`} key={card.task_id} className="recent-card">
                  {card.input_url && (
                    <div className="recent-card-thumb">
                      <img src={card.input_url} alt="" />
                    </div>
                  )}
                  <div className="recent-card-body">
                    <span className="recent-card-emoji">{card.emotion_emoji || em?.emoji || "💭"}</span>
                    <span className="recent-card-title">{card.generated_title || `记录 #${card.task_id}`}</span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>

      <section className="home-section">
        <div className="section-header">
          <h2>每周总结</h2>
          <Link to="/weekly" className="section-link">查看</Link>
        </div>
        <p className="empty-hint-text">在"每周总结"页面生成本周的情绪回顾</p>
      </section>

      <section className="home-cta">
        <Link to="/record" className="btn btn-primary btn-lg">记录此刻</Link>
      </section>
    </div>
  );
}
