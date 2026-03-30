import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiGetTimeline } from '../api/client';
import type { TaskItem } from '../api/types';
import { EMOTION_MAP } from '../api/types';

const PAGE_SIZE = 12;
const VIDEO_RE = /\.(mp4|webm|mov|avi|mkv)(\?|#|$)/i;

function isVideoUrl(url: string | undefined): boolean {
  return !!url && VIDEO_RE.test(url);
}

function truncateText(s: string | undefined, max: number): string {
  if (!s) return '';
  if (s.length <= max) return s;
  return `${s.slice(0, max)}...`;
}

function groupItemsByDate(items: TaskItem[]): { label: string; sortKey: string; items: TaskItem[] }[] {
  const buckets = new Map<string, { label: string; items: TaskItem[] }>();
  for (const item of items) {
    const iso = item.created_at;
    let sortKey: string;
    let label: string;
    if (!iso) {
      sortKey = '__unknown__';
      label = '未知日期';
    } else {
      const d = new Date(iso);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      sortKey = `${y}-${m}-${day}`;
      label = `${y}年${m}月${day}日`;
    }
    if (!buckets.has(sortKey)) buckets.set(sortKey, { label, items: [] });
    buckets.get(sortKey)!.items.push(item);
  }
  const entries = [...buckets.entries()];
  entries.sort((a, b) => {
    if (a[0] === '__unknown__') return 1;
    if (b[0] === '__unknown__') return -1;
    return b[0].localeCompare(a[0]);
  });
  return entries.map(([sortKey, v]) => {
    const sortedItems = [...v.items].sort((a, b) => {
      const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
      const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
      return tb - ta;
    });
    return { sortKey, label: v.label, items: sortedItems };
  });
}

function cardEmoji(task: TaskItem): string {
  if (task.emotion_emoji) return task.emotion_emoji;
  const key = task.emotion ?? '';
  return EMOTION_MAP[key]?.emoji ?? '💭';
}

export default function TimelinePage() {
  const [items, setItems] = useState<TaskItem[]>([]);
  const [loadedPage, setLoadedPage] = useState(0);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await apiGetTimeline({ page: 1, page_size: PAGE_SIZE });
        if (!cancelled) {
          setItems(r.items);
          setPages(r.pages);
          setTotal(r.total);
          setLoadedPage(1);
        }
      } catch {
        /* keep empty */
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const groups = groupItemsByDate(items);
  const hasMore = loadedPage > 0 && loadedPage < pages;

  const handleLoadMore = async () => {
    if (loadingMore || loadedPage <= 0 || loadedPage >= pages) return;
    const nextPage = loadedPage + 1;
    setLoadingMore(true);
    try {
      const r = await apiGetTimeline({ page: nextPage, page_size: PAGE_SIZE });
      setItems((prev) => [...prev, ...r.items]);
      setPages(r.pages);
      setTotal(r.total);
      setLoadedPage(nextPage);
    } catch {
      /* keep previous */
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="timeline-page">
      <div className="page-header">
        <div>
          <h1>
            📖 情绪时间轴
          </h1>
          <p className="page-subtitle">共 {total} 条记录</p>
        </div>
      </div>

      {loading && items.length === 0 ? (
        <div className="empty-state">
          <div className="spinner" />
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <p>还没有情绪记录，去记录第一个画面吧</p>
          <Link to="/record" className="btn btn-primary" style={{ marginTop: 16 }}>
            去记录
          </Link>
        </div>
      ) : (
        <>
          {groups.map((g) => (
            <section key={g.sortKey} className="timeline-date-group">
              <h2 className="timeline-date-header">{g.label}</h2>
              {g.items.map((task) => {
                const input = task.input_url;
                const video = isVideoUrl(input);
                const tags = (task.tags ?? []).slice(0, 3);
                const title = task.generated_title?.trim() || `记录 #${task.task_id}`;
                return (
                  <Link
                    key={task.task_id}
                    to={`/card/${task.task_id}`}
                    className="timeline-card"
                  >
                    <div className="timeline-card-thumb">
                      {video ? (
                        <span aria-hidden>🎬</span>
                      ) : input ? (
                        <img src={input} alt="" />
                      ) : (
                        <span aria-hidden>🖼️</span>
                      )}
                    </div>
                    <div className="timeline-card-body">
                      <div className="timeline-card-title">
                        <span>{cardEmoji(task)}</span>
                        <span>{title}</span>
                      </div>
                      <p className="timeline-card-text">{truncateText(task.generated_text, 60)}</p>
                      {tags.length > 0 && (
                        <div>
                          {tags.map((t, i) => (
                            <span key={`${task.task_id}-tag-${i}`}>{t}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </Link>
                );
              })}
            </section>
          ))}
          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <button
                type="button"
                className="load-more-btn btn btn-primary"
                disabled={loadingMore}
                onClick={() => void handleLoadMore()}
              >
                {loadingMore ? '加载中…' : '加载更多'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
