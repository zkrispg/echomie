import { useState, useRef, useCallback, useEffect, type FormEvent, type DragEvent, type ChangeEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiUpload, apiGetStyles, ApiError } from "../api/client";
import type { StyleInfo } from "../api/types";

const ACCEPT_ATTR =
  ".jpg,.jpeg,.png,.webp,.mp4,.mov,.avi,.mkv,image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/x-msvideo,video/x-matroska";

const EXT_OK = new Set(["jpg", "jpeg", "png", "webp", "mp4", "mov", "avi", "mkv"]);

function isAcceptedFile(f: File): boolean {
  const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
  if (EXT_OK.has(ext)) return true;
  if (f.type.startsWith("image/")) return ["jpeg", "jpg", "png", "webp"].some((x) => f.type.includes(x));
  return ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska", "video/avi"].includes(f.type);
}

export default function RecordPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragover, setDragover] = useState(false);
  const [context, setContext] = useState("");
  const [style, setStyle] = useState("none");
  const [styles, setStyles] = useState<StyleInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [taskId, setTaskId] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    apiGetStyles().then((r) => setStyles(r.styles)).catch(() => {});
  }, []);

  const clearFile = useCallback(() => {
    setFile(null);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const handleFile = useCallback((f: File) => {
    if (!isAcceptedFile(f)) {
      setError("请选择 JPG、PNG、WebP 图片或 MP4、MOV、AVI、MKV 视频");
      return;
    }
    setError("");
    setFile(f);
    if (f.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(f);
    } else {
      setPreview(null);
    }
  }, []);

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragover(true);
  }, []);

  const onDragLeave = useCallback(() => {
    setDragover(false);
  }, []);

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragover(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const onInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const openPicker = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const isVideo = file ? !file.type.startsWith("image/") : false;
  const formatSize = (b: number) =>
    b < 1048576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1048576).toFixed(1)} MB`;

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      if (!file) return;
      setError("");
      setUploading(true);
      try {
        const res = await apiUpload(file, context.trim(), style);
        setTaskId(res.data.task_id);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "上传失败，请重试");
      } finally {
        setUploading(false);
      }
    },
    [file, context, style]
  );

  const resetFlow = useCallback(() => {
    setTaskId(null);
    clearFile();
    setContext("");
    setStyle("none");
    setError("");
  }, [clearFile]);

  if (taskId !== null) {
    return (
      <div className="record-page">
        <div className="success-card">
          <p className="record-success-lead">已收到你的画面</p>
          <p className="record-task-id">
            任务编号 <strong>#{taskId}</strong>
          </p>
          <Link className="record-card-link" to={`/card/${taskId}`}>
            查看疗愈回应
          </Link>
          <div className="record-success-actions">
            <button type="button" className="btn btn-ghost" onClick={resetFlow}>
              再传一张
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="record-page">
      <div className="page-header">
        <h1>记录这一刻</h1>
        <p className="page-subtitle">上传画面，让 AI 感受并回应你</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div
          className={`upload-zone${dragover ? " dragover" : ""}${file ? " has-file" : ""}`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={openPicker}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPicker();
            }
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT_ATTR}
            onChange={onInputChange}
            hidden
          />
          {file ? (
            <div className="preview-area" onClick={(e) => e.stopPropagation()}>
              {preview ? (
                <img src={preview} alt="" className="preview-area-img" />
              ) : (
                <div className="preview-area-placeholder">{isVideo ? "🎬" : "🖼️"}</div>
              )}
              <div className="preview-area-meta">
                <span className="preview-area-name">{file.name}</span>
                <span className="preview-area-size">{formatSize(file.size)}</span>
              </div>
              <button
                type="button"
                className="preview-area-clear"
                onClick={(e) => {
                  e.stopPropagation();
                  clearFile();
                }}
              >
                移除
              </button>
            </div>
          ) : (
            <p className="upload-zone-hint">拖拽文件到此处，或点击选择</p>
          )}
        </div>

        <textarea
          className="context-input"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="可以告诉我画面里的小故事哦（选填）"
          rows={4}
          disabled={uploading}
        />

        {styles.length > 0 && (
          <div className="style-section">
            <h3>选择卡通风格（选填）</h3>
            <div className="style-grid">
              {styles.map((s) => (
                <button
                  type="button"
                  key={s.key}
                  className={`style-card${style === s.key ? " active" : ""}`}
                  onClick={() => setStyle(s.key)}
                  disabled={uploading}
                >
                  <span className="style-emoji">{s.emoji}</span>
                  <span className="style-label">{s.label}</span>
                  <span className="style-desc">{s.desc}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {uploading && <p className="record-loading">AI 正在感受你的画面...</p>}

        <button type="submit" className="submit-btn" disabled={!file || uploading}>
          让 AI 感受这一刻
        </button>
      </form>
    </div>
  );
}
