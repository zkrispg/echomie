import { View, Text, Image, Video } from "@tarojs/components";
import Taro, { useLoad } from "@tarojs/taro";
import { useState, useEffect, useRef, useCallback } from "react";
import { apiGetStatus, apiGeneratePoster, ApiError } from "../../api/client";
import { EMOTION_MAP } from "../../api/types";
import type { TaskStatusResponse } from "../../api/types";
import "./index.scss";

function isVideoUrl(url: string): boolean {
  return /\.(mp4|mov|avi|mkv|webm)(\?|#|$)/i.test(url);
}

export default function CardPage() {
  const [taskId, setTaskId] = useState(0);
  const [task, setTask] = useState<TaskStatusResponse | null>(null);
  const [loadError, setLoadError] = useState("");
  const [showOriginal, setShowOriginal] = useState(false);
  const [posterLoading, setPosterLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useLoad((params) => {
    const id = Number(params?.taskId);
    if (id > 0) setTaskId(id);
  });

  useEffect(() => {
    if (!taskId) return;
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await apiGetStatus(taskId);
        if (cancelled) return;
        setTask(data);
        setLoadError("");
        if (data.status !== "queued" && data.status !== "processing" && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } catch (e) {
        if (cancelled) return;
        setLoadError(e instanceof ApiError ? e.message : "加载失败");
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [taskId]);

  const handleDownload = useCallback((url: string) => {
    if (isVideoUrl(url)) {
      Taro.saveVideoToPhotosAlbum({
        filePath: url,
        fail() { Taro.showToast({ title: "保存失败", icon: "none" }); },
        success() { Taro.showToast({ title: "已保存到相册", icon: "success" }); },
      });
    } else {
      Taro.downloadFile({
        url,
        success(res) {
          Taro.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success() { Taro.showToast({ title: "已保存到相册", icon: "success" }); },
            fail() { Taro.showToast({ title: "保存失败", icon: "none" }); },
          });
        },
        fail() { Taro.showToast({ title: "下载失败", icon: "none" }); },
      });
    }
  }, []);

  const handleCopyText = useCallback(() => {
    if (!task) return;
    const text = [task.generated_title, task.generated_text].filter(Boolean).join("\n\n");
    if (text) {
      Taro.setClipboardData({ data: text });
    }
  }, [task]);

  const handleSharePoster = useCallback(async () => {
    if (!taskId || posterLoading) return;
    setPosterLoading(true);
    try {
      const res = await apiGeneratePoster(taskId);
      Taro.downloadFile({
        url: res.poster_url,
        success(dlRes) {
          Taro.saveImageToPhotosAlbum({
            filePath: dlRes.tempFilePath,
            success() { Taro.showToast({ title: "海报已保存到相册", icon: "success" }); },
            fail() { Taro.showToast({ title: "保存失败", icon: "none" }); },
          });
        },
        fail() { Taro.showToast({ title: "下载失败", icon: "none" }); },
      });
    } catch {
      Taro.showToast({ title: "生成海报失败", icon: "none" });
    } finally {
      setPosterLoading(false);
    }
  }, [taskId, posterLoading]);

  if (!taskId) {
    return (
      <View className="page-wrap"><View className="alert alert-error"><Text>无效的任务 ID</Text></View></View>
    );
  }

  if (loadError && !task) {
    return (
      <View className="page-wrap"><View className="alert alert-error"><Text>{loadError}</Text></View></View>
    );
  }

  if (!task) {
    return <View className="page-wrap"><View className="empty-state"><View className="spinner" /></View></View>;
  }

  if (task.status === "failed") {
    return (
      <View className="page-wrap">
        <View className="alert alert-error"><Text>{task.error_msg || "处理失败"}</Text></View>
      </View>
    );
  }

  if (task.status === "queued" || task.status === "processing") {
    return (
      <View className="page-wrap card-page">
        <Text className="progress-label">{task.status === "queued" ? "排队中…" : "AI 分析中…"}</Text>
        <View className="progress-bar">
          <View className="progress-fill" style={{ width: `${Math.min(100, task.progress)}%` }} />
        </View>
        <Text className="progress-pct">{task.progress}%</Text>
      </View>
    );
  }

  const key = task.emotion?.toLowerCase() ?? "";
  const mapped = key ? EMOTION_MAP[key] : undefined;
  const emoji = mapped?.emoji ?? task.emotion_emoji ?? "💭";
  const label = mapped?.label ?? task.emotion ?? "情绪";
  const accent = mapped?.color;

  const inputUrl = task.input_url;
  const outputUrl = task.output_url;
  const hasStyledOutput = !!(outputUrl && inputUrl && outputUrl !== inputUrl);
  const mainMedia = hasStyledOutput ? (showOriginal ? inputUrl! : outputUrl!) : (outputUrl || inputUrl);
  const isVideo = mainMedia ? isVideoUrl(mainMedia) : false;

  return (
    <View className="page-wrap card-page">
      {mainMedia && (
        <View className="card-hero">
          {isVideo ? (
            <Video src={mainMedia} className="card-hero-media" controls />
          ) : (
            <Image src={mainMedia} className="card-hero-media" mode="widthFix" />
          )}
        </View>
      )}

      {hasStyledOutput && (
        <View className="compare-bar">
          <Text
            className={`compare-tab${!showOriginal ? " active" : ""}`}
            onClick={() => setShowOriginal(false)}
          >🎨 风格化</Text>
          <Text
            className={`compare-tab${showOriginal ? " active" : ""}`}
            onClick={() => setShowOriginal(true)}
          >🖼️ 原图</Text>
        </View>
      )}

      <View className="card-actions">
        {hasStyledOutput && outputUrl && (
          <View className="action-btn primary" onClick={() => handleDownload(outputUrl)}>
            <Text>⬇️ 保存风格化</Text>
          </View>
        )}
        {inputUrl && (
          <View className="action-btn" onClick={() => handleDownload(inputUrl)}>
            <Text>{isVideo ? "🎬" : "🖼️"} {hasStyledOutput ? "保存原图" : "保存"}</Text>
          </View>
        )}
        {task.generated_text && (
          <View className="action-btn" onClick={handleCopyText}>
            <Text>📋 复制文案</Text>
          </View>
        )}
        <View className={`action-btn share${posterLoading ? " disabled" : ""}`} onClick={handleSharePoster}>
          <Text>{posterLoading ? "⏳ 生成中…" : "🎴 分享海报"}</Text>
        </View>
      </View>

      <View className="emotion-badge" style={accent ? { borderColor: accent, background: `${accent}22` } : {}}>
        <Text className="emotion-emoji">{emoji}</Text>
        <Text className="emotion-label">{label}</Text>
      </View>

      {task.generated_title && <Text className="card-title">{task.generated_title}</Text>}

      {task.generated_text && (
        <View className="healing-card"><Text>{task.generated_text}</Text></View>
      )}

      {(task.tags ?? []).length > 0 && (
        <View className="tag-pills">
          {task.tags.map((t) => <Text key={t} className="tag-pill">{t}</Text>)}
        </View>
      )}

      {task.voice_url && (
        <View className="voice-section">
          <View
            className="btn btn-ghost btn-block"
            onClick={() => {
              const audio = Taro.createInnerAudioContext();
              audio.src = task.voice_url!;
              audio.play();
            }}
          >
            <Text>🔊 播放治愈语音</Text>
          </View>
        </View>
      )}

      {task.scene_description && (
        <Text className="scene-desc">{task.scene_description}</Text>
      )}

      {task.user_context && (
        <View className="user-context">
          <Text className="context-label">你的想法</Text>
          <Text className="context-text">{task.user_context}</Text>
        </View>
      )}
    </View>
  );
}
