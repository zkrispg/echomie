import { View, Text, Image } from "@tarojs/components";
import Taro, { useDidShow } from "@tarojs/taro";
import { useState } from "react";
import { apiGetTimeline, hasToken } from "../../api/client";
import { EMOTION_MAP } from "../../api/types";
import type { TaskItem } from "../../api/types";
import "./index.scss";

const PAGE_SIZE = 12;

function groupByDate(items: TaskItem[]) {
  const m = new Map<string, { label: string; items: TaskItem[] }>();
  for (const item of items) {
    const iso = item.created_at;
    let key: string, label: string;
    if (!iso) { key = "__unknown__"; label = "未知日期"; }
    else {
      const d = new Date(iso);
      key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      label = `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
    }
    if (!m.has(key)) m.set(key, { label, items: [] });
    m.get(key)!.items.push(item);
  }
  return [...m.entries()]
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([k, v]) => ({ key: k, label: v.label, items: v.items }));
}

export default function TimelinePage() {
  const [items, setItems] = useState<TaskItem[]>([]);
  const [page, setPage] = useState(0);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useDidShow(() => {
    if (!hasToken()) { Taro.redirectTo({ url: "/pages/login/index" }); return; }
    setLoading(true);
    apiGetTimeline({ page: 1, page_size: PAGE_SIZE }).then((r) => {
      setItems(r.items); setPages(r.pages); setTotal(r.total); setPage(1);
    }).catch(() => {}).finally(() => setLoading(false));
  });

  const loadMore = async () => {
    if (loadingMore || page >= pages) return;
    setLoadingMore(true);
    try {
      const r = await apiGetTimeline({ page: page + 1, page_size: PAGE_SIZE });
      setItems((prev) => [...prev, ...r.items]);
      setPages(r.pages); setTotal(r.total); setPage(page + 1);
    } catch {} finally { setLoadingMore(false); }
  };

  const groups = groupByDate(items);

  return (
    <View className="page-wrap timeline-page">
      <Text className="page-title">📖 情绪时间轴</Text>
      <Text className="page-subtitle">共 {total} 条记录</Text>

      {loading && items.length === 0 ? (
        <View className="empty-state"><View className="spinner" /></View>
      ) : items.length === 0 ? (
        <View className="empty-state">
          <Text style={{ color: "#a89bb5" }}>还没有记录</Text>
        </View>
      ) : (
        <View>
          {groups.map((g) => (
            <View key={g.key} className="date-group">
              <Text className="date-header">{g.label}</Text>
              {g.items.map((task) => {
                const em = EMOTION_MAP[task.emotion ?? ""];
                const cardEmoji = task.emotion_emoji || em?.emoji || "💭";
                const title = task.generated_title?.trim() || `记录 #${task.task_id}`;
                return (
                  <View
                    key={task.task_id}
                    className="tl-card"
                    onClick={() => Taro.navigateTo({ url: `/pages/card/index?taskId=${task.task_id}` })}
                  >
                    <View className="tl-thumb">
                      {task.input_url ? (
                        <Image className="tl-thumb-img" src={task.input_url} mode="aspectFill" />
                      ) : (
                        <Text style={{ fontSize: "48rpx" }}>🖼️</Text>
                      )}
                    </View>
                    <View className="tl-body">
                      <View className="tl-title-row">
                        <Text>{cardEmoji} </Text>
                        <Text className="tl-title">{title}</Text>
                      </View>
                      {task.generated_text && (
                        <Text className="tl-text">
                          {task.generated_text.length > 40 ? task.generated_text.slice(0, 40) + "..." : task.generated_text}
                        </Text>
                      )}
                    </View>
                  </View>
                );
              })}
            </View>
          ))}
          {page < pages && (
            <View className="btn btn-primary btn-block" style={{ marginTop: "32rpx" }} onClick={loadMore}>
              <Text style={{ color: "#fff" }}>{loadingMore ? "加载中…" : "加载更多"}</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}
