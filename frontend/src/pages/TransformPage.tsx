import { useState, useRef, useEffect, type FormEvent, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { apiUpload, apiGetStyles, ApiError } from "../api/client";
import type { StyleInfo } from "../api/types";

const ACCEPTED = ".mp4,.mov,.avi,.mkv,.jpg,.jpeg,.png,.webp";

export default function TransformPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [styles, setStyles] = useState<StyleInfo[]>([]);
  const [selectedStyle, setSelectedStyle] = useState("warm_cartoon");
  const [title, setTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [taskId, setTaskId] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    apiGetStyles().then((r) => setStyles(r.styles)).catch(() => {});
  }, []);

  const handleFile = (f: File) => {
    setFile(f);
    if (f.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(f);
    } else {
      setPreview(null);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const isVideo = file ? /\.(mp4|mov|avi|mkv)$/i.test(file.name) : false;
  const formatSize = (b: number) => b < 1048576 ? (b / 1024).toFixed(1) + " KB" : (b / 1048576).toFixed(1) + " MB";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      const res = await apiUpload(file, selectedStyle, title);
      setTaskId(res.data.task_id as number);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "上传失败，请重试");
    } finally {
      setUploading(false);
    }
  };

  if (taskId !== null) {
    const styleInfo = styles.find((s) => s.key === selectedStyle);
    return (
      <div className="transform-page">
        <div className="success-card">
          <div className="success-icon">🎉</div>
          <h2>创作已开始！</h2>
          <p>任务 <strong>#{taskId}</strong> · {styleInfo?.emoji} {styleInfo?.label || selectedStyle}</p>
          <p className="success-hint">AI 正在为你施展魔法，稍等片刻就能看到效果~</p>
          <div className="success-actions">
            <button className="btn btn-primary" onClick={() => navigate("/tasks")}>查看进度 ✨</button>
            <button className="btn btn-ghost" onClick={() => { setTaskId(null); setFile(null); setPreview(null); setTitle(""); }}>
              继续创作
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="transform-page">
      <div className="page-header">
        <h1>🎨 AI 变身工坊</h1>
        <p className="page-subtitle">上传你的照片或视频，让 AI 赋予它治愈的卡通灵魂</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div
          className={`drop-zone ${dragOver ? "drag-over" : ""} ${file ? "has-file" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input ref={inputRef} type="file" accept={ACCEPTED} onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} hidden />
          {file ? (
            <div className="file-preview-row">
              {preview ? (
                <img src={preview} alt="preview" className="file-thumb" />
              ) : (
                <div className="file-thumb-placeholder">{isVideo ? "🎬" : "🖼️"}</div>
              )}
              <div className="file-meta">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{formatSize(file.size)}</span>
              </div>
              <button type="button" className="btn-remove" onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(null); }}>✕</button>
            </div>
          ) : (
            <div className="drop-zone-content">
              <div className="drop-emoji">📸</div>
              <p className="drop-text">拖拽文件到这里，或点击选择</p>
              <p className="drop-hint">支持 JPG / PNG / MP4 / MOV 等格式</p>
            </div>
          )}
        </div>

        <div className="form-group" style={{ marginTop: 20 }}>
          <label>给这次创作起个名字（可选）</label>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="例如：夏日回忆、我家猫咪..." />
        </div>

        <div className="style-section">
          <h3>选择变身风格 ✨</h3>
          <div className="style-grid">
            {styles.map((s) => (
              <button
                key={s.key}
                type="button"
                className={`style-card ${selectedStyle === s.key ? "active" : ""}`}
                onClick={() => setSelectedStyle(s.key)}
              >
                <span className="style-emoji">{s.emoji}</span>
                <span className="style-label">{s.label}</span>
                <span className="style-desc">{s.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={!file || uploading}>
          {uploading ? "上传中..." : `开始 AI 变身 ✨`}
        </button>
      </form>
    </div>
  );
}
