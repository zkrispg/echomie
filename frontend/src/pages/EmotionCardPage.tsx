import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiGetStatus, ApiError } from "../api/client";
import { EMOTION_MAP } from "../api/types";
import type { TaskStatusResponse } from "../api/types";

function downloadFile(url: string, filename?: string) {
  fetch(url)
    .then(r => r.blob())
    .then(blob => {
      const a = document.createElement("a");
      const blobUrl = URL.createObjectURL(blob);
      a.href = blobUrl;
      a.download = filename || url.split("/").pop() || "download";
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(blobUrl); a.remove(); }, 200);
    })
    .catch(() => { window.open(url, "_blank"); });
}

function isVideoUrl(url: string): boolean {
  try {
    const path = new URL(url, window.location.origin).pathname;
    return /\.(mp4|mov|avi|mkv|webm)$/i.test(path);
  } catch {
    return /\.(mp4|mov|avi|mkv|webm)$/i.test(url);
  }
}

function emotionDisplay(task: TaskStatusResponse) {
  const key = task.emotion?.toLowerCase() ?? "";
  const mapped = key ? EMOTION_MAP[key] : undefined;
  return {
    emoji: mapped?.emoji ?? task.emotion_emoji ?? "💭",
    label: mapped?.label ?? task.emotion ?? "情绪",
    accent: mapped?.color,
  };
}

export default function EmotionCardPage() {
  const { taskId: taskIdParam } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<TaskStatusResponse | null>(null);
  const [loadError, setLoadError] = useState("");
  const [badId, setBadId] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const taskIdNum = taskIdParam ? Number(taskIdParam) : NaN;

  useEffect(() => {
    if (!taskIdParam || !Number.isFinite(taskIdNum)) {
      setBadId(true);
      return;
    }

    let cancelled = false;

    const poll = async () => {
      try {
        const data = await apiGetStatus(taskIdNum);
        if (cancelled) return;
        setTask(data);
        setLoadError("");
        const polling =
          data.status === "queued" || data.status === "processing";
        if (!polling && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } catch (e) {
        if (cancelled) return;
        setLoadError(e instanceof ApiError ? e.message : "加载失败，请稍后重试");
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 3000);

    return () => {
      cancelled = true;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [taskIdParam, taskIdNum]);

  if (badId) {
    return (
      <div className="emotion-card-page">
        <div className="alert alert-error">无效的任务 ID</div>
        <Link to="/timeline" className="btn btn-ghost">← 返回时间线</Link>
      </div>
    );
  }

  if (loadError && !task) {
    return (
      <div className="emotion-card-page">
        <div className="alert alert-error">{loadError}</div>
        <Link to="/timeline" className="btn btn-ghost">← 返回时间线</Link>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="emotion-card-page">
        <div className="empty-state">
          <div className="spinner" />
        </div>
      </div>
    );
  }

  if (task.status === "failed") {
    return (
      <div className="emotion-card-page">
        <Link to="/timeline" className="btn btn-ghost emotion-card-back">← 返回时间线</Link>
        <div className="alert alert-error">{task.error_msg || "处理失败"}</div>
      </div>
    );
  }

  const showProgress = task.status === "queued" || task.status === "processing";

  if (showProgress) {
    return (
      <div className="emotion-card-page">
        <Link to="/timeline" className="btn btn-ghost emotion-card-back">← 返回时间线</Link>
        <div className="progress-section">
          <p className="progress-section-label">
            {task.status === "queued" ? "排队中…" : "AI 分析中…"}
          </p>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${Math.min(100, Math.max(0, task.progress))}%` }} />
            <span className="progress-pct">{task.progress}%</span>
          </div>
        </div>
      </div>
    );
  }

  const { emoji, label, accent } = emotionDisplay(task);
  const inputUrl = task.input_url;
  const outputUrl = task.output_url;
  const hasStyledOutput = !!(outputUrl && inputUrl && outputUrl !== inputUrl);
  const tags = task.tags ?? [];
  const mainMedia = hasStyledOutput ? (showOriginal ? inputUrl! : outputUrl!) : (outputUrl || inputUrl);
  const isVideo = mainMedia ? isVideoUrl(mainMedia) : false;

  const handleCopyText = () => {
    const text = [task.generated_title, task.generated_text].filter(Boolean).join("\n\n");
    if (text) navigator.clipboard.writeText(text).catch(() => {});
  };

  const handleDownload = useCallback((url: string, prefix: string) => {
    const ext = url.split(".").pop()?.split("?")[0] || "jpg";
    downloadFile(url, `echomie_${prefix}_${taskIdNum}.${ext}`);
  }, [taskIdNum]);

  return (
    <div className="emotion-card-page">
      <Link to="/timeline" className="btn btn-ghost emotion-card-back">← 返回时间线</Link>

      {mainMedia && (
        <div className="card-hero">
          {isVideo ? (
            <video src={mainMedia} className="card-hero-media" controls playsInline />
          ) : (
            <img src={mainMedia} alt="媒体" className="card-hero-media" />
          )}
        </div>
      )}

      {hasStyledOutput && (
        <div className="card-compare-bar">
          <button
            type="button"
            className={`compare-tab${!showOriginal ? " active" : ""}`}
            onClick={() => setShowOriginal(false)}
          >
            🎨 风格化
          </button>
          <button
            type="button"
            className={`compare-tab${showOriginal ? " active" : ""}`}
            onClick={() => setShowOriginal(true)}
          >
            🖼️ 原图
          </button>
        </div>
      )}

      <div className="card-actions">
        {hasStyledOutput && outputUrl && (
          <button type="button" className="card-action-btn primary" onClick={() => handleDownload(outputUrl, "styled")}>
            <span className="card-action-icon">⬇️</span>
            <span>保存风格化</span>
          </button>
        )}
        {inputUrl && (
          <button type="button" className="card-action-btn" onClick={() => handleDownload(inputUrl, "original")}>
            <span className="card-action-icon">{isVideo ? "🎬" : "🖼️"}</span>
            <span>{hasStyledOutput ? "保存原图" : (isVideo ? "保存视频" : "保存图片")}</span>
          </button>
        )}
        {task.generated_text && (
          <button type="button" className="card-action-btn" onClick={handleCopyText}>
            <span className="card-action-icon">📋</span>
            <span>复制文案</span>
          </button>
        )}
      </div>

      <div
        className="card-emotion-badge"
        style={accent ? { borderColor: accent, background: `${accent}22` } : undefined}
      >
        <span className="card-emotion-emoji" aria-hidden>{emoji}</span>
        <span className="card-emotion-label">{label}</span>
      </div>

      {task.generated_title && (
        <h1 className="card-title">{task.generated_title}</h1>
      )}

      {task.generated_text && (
        <div className="healing-text-card">{task.generated_text}</div>
      )}

      {tags.length > 0 && (
        <div className="tag-pills">
          {tags.map((t) => (
            <span key={t} className="tag-pill">{t}</span>
          ))}
        </div>
      )}

      {task.voice_url && (
        <div className="voice-player">
          <audio src={task.voice_url} controls className="voice-audio" />
        </div>
      )}

      {task.scene_description && (
        <p className="scene-desc">{task.scene_description}</p>
      )}

      {task.user_context && (
        <div className="user-context-block">
          <span className="user-context-label">你的想法</span>
          <p className="user-context-text">{task.user_context}</p>
        </div>
      )}
    </div>
  );
}
