import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { apiGetTasks, apiCancelTask, apiRetryTask, apiDeleteTask, ApiError } from "../api/client";
import type { TaskItem } from "../api/types";

const FILTERS = [
  { value: "", label: "全部" },
  { value: "queued", label: "🕐 排队中" },
  { value: "processing", label: "⏳ 处理中" },
  { value: "completed", label: "✅ 已完成" },
  { value: "failed", label: "❌ 失败" },
];

function formatTime(iso?: string) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function TaskCard({ task, onRefresh }: { task: TaskItem; onRefresh: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const action = async (fn: () => Promise<unknown>) => {
    setError("");
    setLoading(true);
    try { await fn(); onRefresh(); } catch (e) { setError(e instanceof ApiError ? e.message : "操作失败"); }
    setLoading(false);
  };

  const title = task.generated_title || `#${task.task_id}`;
  const emoji = task.emotion_emoji || "💭";

  return (
    <div className={`task-card status-${task.status}`}>
      <div className="task-card-header">
        <span className="task-title">{emoji} {title}</span>
        <span className={`badge-sm status-${task.status}`}>
          {task.status === "completed" ? "✅ 完成" : task.status === "processing" ? "⏳ 处理中" : task.status === "queued" ? "🕐 排队" : "❌ 失败"}
        </span>
      </div>
      {task.emotion && <div className="task-style-tag">{task.emotion}</div>}
      {(task.status === "processing" || task.status === "queued") && (
        <div className="progress-bar"><div className="progress-fill" style={{ width: `${task.progress}%` }} /><span className="progress-pct">{task.progress}%</span></div>
      )}
      {task.error_msg && <div className="task-error">{task.error_msg}</div>}
      {error && <div className="task-error">{error}</div>}
      <div className="task-card-footer">
        <span className="task-time">{formatTime(task.created_at)}</span>
        <div className="task-actions">
          {task.status === "completed" && (
            <Link to={`/card/${task.task_id}`} className="btn btn-sm btn-primary">查看</Link>
          )}
          {(task.status === "queued" || task.status === "processing") && (
            <button className="btn btn-sm btn-warning" onClick={() => action(() => apiCancelTask(task.task_id))} disabled={loading}>取消</button>
          )}
          {task.status === "failed" && (
            <button className="btn btn-sm btn-primary" onClick={() => action(() => apiRetryTask(task.task_id))} disabled={loading}>重试</button>
          )}
          {task.status !== "processing" && (
            <button className="btn btn-sm btn-danger" onClick={() => { if (confirm("确定删除？")) action(() => apiDeleteTask(task.task_id)); }} disabled={loading}>删除</button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await apiGetTasks({ page, page_size: 12, status: filter || undefined, sort: "id_desc" });
      setTasks(r.items); setPages(r.pages); setTotal(r.total);
    } catch { /* */ }
    setLoading(false);
  }, [page, filter]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const active = tasks.some((t) => t.status === "queued" || t.status === "processing");
    if (!active) return;
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [tasks, load]);

  return (
    <div className="tasks-page">
      <div className="page-header">
        <div>
          <h1>📋 我的任务</h1>
          <p className="page-subtitle">共 {total} 个任务</p>
        </div>
        <Link to="/record" className="btn btn-primary">📷 记录此刻</Link>
      </div>
      <div className="filter-bar">
        {FILTERS.map((f) => (
          <button key={f.value} className={`filter-chip ${filter === f.value ? "active" : ""}`} onClick={() => { setFilter(f.value); setPage(1); }}>
            {f.label}
          </button>
        ))}
      </div>
      {loading && tasks.length === 0 ? (
        <div className="empty-state"><div className="spinner" /></div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-emoji">📭</div>
          <h3>暂无任务</h3>
          <Link to="/record" className="btn btn-primary" style={{ marginTop: 12 }}>去记录</Link>
        </div>
      ) : (
        <>
          <div className="task-grid">{tasks.map((t) => <TaskCard key={t.task_id} task={t} onRefresh={load} />)}</div>
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
