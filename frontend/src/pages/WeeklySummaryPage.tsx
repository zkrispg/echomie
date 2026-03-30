import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { apiGetWeeklySummaries, apiGenerateWeeklySummary } from "../api/client";
import type { WeeklySummaryItem } from "../api/types";

function formatWeekRange(weekStart: string, weekEnd: string): string {
  const start = new Date(weekStart);
  const end = new Date(weekEnd);
  const opts: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
  };
  return `${start.toLocaleDateString("zh-CN", opts)} ~ ${end.toLocaleDateString("zh-CN", opts)}`;
}

export default function WeeklySummaryPage() {
  const [items, setItems] = useState<WeeklySummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadList = async () => {
    try {
      const res = await apiGetWeeklySummaries(20);
      setItems(res.items);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadList();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await apiGenerateWeeklySummary();
      await loadList();
    } catch (e) {
      alert(e instanceof Error ? e.message : "生成失败，请稍后再试");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="weekly-page">
      <header className="page-header">
        <div>
          <h1>
            📊 每周情绪总结
          </h1>
        </div>
        <button
          type="button"
          className="btn btn-primary weekly-generate-btn"
          onClick={handleGenerate}
          disabled={generating || loading}
        >
          {generating ? "生成中…" : "生成本周总结"}
        </button>
      </header>

      {loading ? (
        <div className="empty-state">
          <div className="spinner" style={{ margin: "0 auto" }} />
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-emoji">📋</div>
          <p>还没有周报，完成一些情绪记录后来生成吧</p>
          <p style={{ marginTop: 12 }}>
            <Link to="/record">去记录情绪</Link>
          </p>
        </div>
      ) : (
        <ul>
          {items.map((row) => (
            <li key={row.id} className="weekly-card">
              <div className="weekly-card-range">{formatWeekRange(row.week_start, row.week_end)}</div>
              {row.summary_text != null && row.summary_text !== "" && (
                <p className="weekly-card-text">{row.summary_text}</p>
              )}
              {row.mood_trend != null && row.mood_trend !== "" && (
                <p className="weekly-card-trend">{row.mood_trend}</p>
              )}
              {row.tags.length > 0 && (
                <div className="weekly-tags">
                  {row.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              )}
              {row.encouragement != null && row.encouragement !== "" && (
                <div className="weekly-card-encouragement">{row.encouragement}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
