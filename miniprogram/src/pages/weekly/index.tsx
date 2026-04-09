import { View, Text } from "@tarojs/components";
import Taro from "@tarojs/taro";
import { useState, useEffect } from "react";
import { apiGetWeeklySummaries, apiGenerateWeeklySummary } from "../../api/client";
import type { WeeklySummaryItem } from "../../api/types";
import "./index.scss";

function formatRange(s: string, e: string): string {
  const start = new Date(s);
  const end = new Date(e);
  return `${start.getFullYear()}年${start.getMonth() + 1}月${start.getDate()}日 ~ ${end.getMonth() + 1}月${end.getDate()}日`;
}

export default function WeeklyPage() {
  const [items, setItems] = useState<WeeklySummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const load = () => {
    apiGetWeeklySummaries(20).then((r) => setItems(r.items)).catch(() => setItems([])).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await apiGenerateWeeklySummary();
      load();
    } catch (e: any) {
      Taro.showToast({ title: e.message || "生成失败", icon: "none" });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <View className="page-wrap weekly-page">
      <View className="header-row">
        <Text className="page-title">📊 每周情绪总结</Text>
        <View
          className={`btn btn-primary gen-btn${generating || loading ? " disabled" : ""}`}
          onClick={generating || loading ? undefined : handleGenerate}
        >
          <Text style={{ color: "#fff", fontSize: "24rpx" }}>{generating ? "生成中…" : "生成本周总结"}</Text>
        </View>
      </View>

      {loading ? (
        <View className="empty-state"><View className="spinner" /></View>
      ) : items.length === 0 ? (
        <View className="empty-state">
          <Text className="empty-emoji">📋</Text>
          <Text style={{ color: "#a89bb5" }}>还没有周报，完成一些情绪记录后来生成吧</Text>
        </View>
      ) : (
        <View className="weekly-list">
          {items.map((row) => (
            <View key={row.id} className="weekly-card">
              <Text className="weekly-range">{formatRange(row.week_start, row.week_end)}</Text>
              {row.summary_text && <Text className="weekly-text">{row.summary_text}</Text>}
              {row.mood_trend && <Text className="weekly-trend">{row.mood_trend}</Text>}
              {row.tags.length > 0 && (
                <View className="weekly-tags">
                  {row.tags.map((tag) => <Text key={tag} className="weekly-tag">{tag}</Text>)}
                </View>
              )}
              {row.encouragement && (
                <View className="weekly-enc"><Text>{row.encouragement}</Text></View>
              )}
            </View>
          ))}
        </View>
      )}
    </View>
  );
}
