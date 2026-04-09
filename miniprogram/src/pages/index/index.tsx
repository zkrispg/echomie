import { View, Text, Image } from "@tarojs/components";
import Taro, { useDidShow } from "@tarojs/taro";
import { useState } from "react";
import { hasToken, apiGetMe, apiGetAffirmation, apiCreateMood, apiGetMoods, apiGetTimeline } from "../../api/client";
import { MOOD_OPTIONS, EMOTION_MAP } from "../../api/types";
import type { UserMe, MoodItem, TaskItem } from "../../api/types";
import "./index.scss";

export default function IndexPage() {
  const [user, setUser] = useState<UserMe | null>(null);
  const [affirmation, setAffirmation] = useState("");
  const [selectedMood, setSelectedMood] = useState("");
  const [recentMoods, setRecentMoods] = useState<MoodItem[]>([]);
  const [recentCards, setRecentCards] = useState<TaskItem[]>([]);

  useDidShow(() => {
    if (!hasToken()) {
      Taro.redirectTo({ url: "/pages/login/index" });
      return;
    }
    apiGetMe().then(setUser).catch(() => {
      Taro.redirectTo({ url: "/pages/login/index" });
    });
    apiGetAffirmation("okay").then((r) => setAffirmation(r.affirmation)).catch(() => {});
    apiGetMoods(5).then((r) => setRecentMoods(r.items)).catch(() => {});
    apiGetTimeline({ page: 1, page_size: 3 }).then((r) => setRecentCards(r.items)).catch(() => {});
  });

  const handleMood = async (mood: string, emoji: string) => {
    try {
      const r = await apiCreateMood({ mood, emoji });
      setSelectedMood(mood);
      if (r.affirmation) setAffirmation(r.affirmation);
      apiGetMoods(5).then((res) => setRecentMoods(res.items)).catch(() => {});
    } catch {}
  };

  return (
    <View className="page-wrap home-page">
      <View className="home-greeting">
        <Text className="greeting-text">{user?.avatar_emoji || "🌸"} 你好，{user?.username || ""}</Text>
        {affirmation && <View className="home-affirmation"><Text>{affirmation}</Text></View>}
      </View>

      <View className="section">
        <Text className="section-title">今日心情打卡</Text>
        <View className="mood-grid">
          {MOOD_OPTIONS.map((opt) => (
            <View
              key={opt.mood}
              className={`mood-btn${selectedMood === opt.mood ? " active" : ""}`}
              onClick={() => handleMood(opt.mood, opt.emoji)}
            >
              <Text className="mood-emoji">{opt.emoji}</Text>
              <Text className="mood-label">{opt.label}</Text>
            </View>
          ))}
        </View>
      </View>

      <View className="section">
        <View className="section-header">
          <Text className="section-title">最近情绪记录</Text>
          <Text className="section-link" onClick={() => Taro.switchTab({ url: "/pages/timeline/index" })}>查看全部</Text>
        </View>
        {recentCards.length === 0 ? (
          <View className="empty-hint">
            <Text style={{ color: "#a89bb5" }}>还没有记录</Text>
          </View>
        ) : (
          <View className="recent-grid">
            {recentCards.map((card) => {
              const em = EMOTION_MAP[card.emotion || ""] || null;
              return (
                <View
                  key={card.task_id}
                  className="recent-card"
                  onClick={() => Taro.navigateTo({ url: `/pages/card/index?taskId=${card.task_id}` })}
                >
                  {card.input_url && (
                    <Image className="recent-thumb" src={card.input_url} mode="aspectFill" />
                  )}
                  <View className="recent-body">
                    <Text className="recent-emoji">{card.emotion_emoji || em?.emoji || "💭"}</Text>
                    <Text className="recent-title">{card.generated_title || `记录 #${card.task_id}`}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </View>

      <View className="section">
        <View className="section-header">
          <Text className="section-title">每周总结</Text>
          <Text className="section-link" onClick={() => Taro.navigateTo({ url: "/pages/weekly/index" })}>查看</Text>
        </View>
        <Text style={{ fontSize: "26rpx", color: "#a89bb5" }}>在每周总结页面生成本周的情绪回顾</Text>
      </View>

      <View className="section">
        <Text className="section-title">更多功能</Text>
        <View className="quick-grid">
          <View className="quick-card" onClick={() => Taro.navigateTo({ url: "/pages/chat/index" })}>
            <Text className="quick-icon">💬</Text>
            <Text className="quick-label">AI 陪伴</Text>
            <Text className="quick-desc">和 AI 聊聊心事</Text>
          </View>
          <View className="quick-card" onClick={() => Taro.navigateTo({ url: "/pages/music/index" })}>
            <Text className="quick-icon">🎵</Text>
            <Text className="quick-label">音乐治愈</Text>
            <Text className="quick-desc">让音乐抚慰心灵</Text>
          </View>
        </View>
      </View>
    </View>
  );
}
