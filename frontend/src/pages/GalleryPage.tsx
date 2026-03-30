import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { apiGetGallery } from "../api/client";
import type { TaskItem } from "../api/types";

export default function GalleryPage() {
  const [items, setItems] = useState<TaskItem[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const r = await apiGetGallery({ page, page_size: 12 });
      setItems(r.items);
      setPages(r.pages);
      setTotal(r.total);
    } catch { /* */ }
    setLoading(false);
  }, [page]);

  useEffect(() => { fetch(); }, [fetch]);

  return (
    <div className="gallery-page">
      <div className="page-header">
        <div>
          <h1>🖼️ 治愈画廊</h1>
          <p className="page-subtitle">每一幅作品，都是你内心世界的投影 · 共 {total} 幅</p>
        </div>
        <Link to="/transform" className="btn btn-primary">✨ 创建新作品</Link>
      </div>

      {loading && items.length === 0 ? (
        <div className="empty-state">
          <div className="spinner" />
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-emoji">🎨</div>
          <h3>画廊还是空的</h3>
          <p>去创作第一幅治愈系作品吧！</p>
          <Link to="/transform" className="btn btn-primary" style={{ marginTop: 16 }}>开始创作</Link>
        </div>
      ) : (
        <>
          <div className="gallery-grid">
            {items.map((item) => (
              <div key={item.task_id} className="gallery-card">
                <div className="gallery-card-image">
                  {item.output_url ? (
                    item.output_url.match(/\.(mp4|mov|avi|mkv)$/i) ? (
                      <video src={item.output_url} className="gallery-media" muted loop
                        onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
                        onMouseLeave={(e) => { const v = e.target as HTMLVideoElement; v.pause(); v.currentTime = 0; }}
                      />
                    ) : (
                      <img src={item.output_url} alt={item.title || ""} className="gallery-media" />
                    )
                  ) : (
                    <div className="gallery-placeholder">🎨</div>
                  )}
                </div>
                <div className="gallery-card-info">
                  <span className="gallery-title">{item.title || `作品 #${item.task_id}`}</span>
                  <span className="gallery-style">{item.style}</span>
                </div>
                <div className="gallery-card-actions">
                  {item.output_url && (
                    <a href={item.output_url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-primary">
                      下载 💾
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
          {pages > 1 && (
            <div className="pagination">
              <button className="btn btn-sm btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</button>
              <span className="page-info">{page} / {pages}</span>
              <button className="btn btn-sm btn-ghost" disabled={page >= pages} onClick={() => setPage(p => p + 1)}>下一页</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
