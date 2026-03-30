import { useState, useEffect, type FormEvent } from "react";
import { useAuth } from "../contexts/AuthContext";
import { apiChangePassword, apiUpdateAvatar, apiGetMoods, ApiError } from "../api/client";
import type { MoodItem } from "../api/types";

const AVATAR_OPTIONS = ["🌸", "🦋", "🌈", "🧸", "🐱", "🐶", "🌻", "🍀", "🦊", "🐰", "🌙", "⭐", "🎀", "🍓", "🌺", "💜"];

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const [oldPwd, setOldPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdError, setPwdError] = useState("");
  const [pwdSuccess, setPwdSuccess] = useState("");
  const [moods, setMoods] = useState<MoodItem[]>([]);
  const [showAvatarPicker, setShowAvatarPicker] = useState(false);

  useEffect(() => {
    apiGetMoods(20).then((r) => setMoods(r.items)).catch(() => {});
  }, []);

  const handleAvatar = async (emoji: string) => {
    try {
      await apiUpdateAvatar(emoji);
      await refresh();
      setShowAvatarPicker(false);
    } catch { /* */ }
  };

  const handleChangePwd = async (e: FormEvent) => {
    e.preventDefault();
    setPwdError(""); setPwdSuccess("");
    if (newPwd !== confirmPwd) { setPwdError("两次密码不一致"); return; }
    if (newPwd.length < 6) { setPwdError("新密码至少6位"); return; }
    setPwdLoading(true);
    try {
      await apiChangePassword(oldPwd, newPwd);
      setPwdSuccess("密码修改成功 🎉");
      setOldPwd(""); setNewPwd(""); setConfirmPwd("");
    } catch (err) {
      setPwdError(err instanceof ApiError ? err.detail : "修改失败");
    }
    setPwdLoading(false);
  };

  const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString("zh-CN") : "-";

  return (
    <div className="profile-page">
      <div className="page-header"><h1>💜 个人中心</h1></div>
      <div className="profile-grid">
        <div className="card">
          <div className="card-body" style={{ textAlign: "center" }}>
            <div className="profile-avatar-large" onClick={() => setShowAvatarPicker(!showAvatarPicker)} style={{ cursor: "pointer" }}>
              {user?.avatar_emoji || "🌸"}
            </div>
            {showAvatarPicker && (
              <div className="avatar-picker">
                {AVATAR_OPTIONS.map((e) => (
                  <button key={e} className={`avatar-opt ${user?.avatar_emoji === e ? "active" : ""}`} onClick={() => handleAvatar(e)}>{e}</button>
                ))}
              </div>
            )}
            <h2 style={{ margin: "12px 0 4px" }}>{user?.username}</h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.87rem" }}>{user?.email}</p>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 8 }}>加入于 {formatDate(user?.created_at)}</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>🔒 修改密码</h3></div>
          <div className="card-body">
            {pwdError && <div className="alert alert-error">{pwdError}</div>}
            {pwdSuccess && <div className="alert alert-success">{pwdSuccess}</div>}
            <form onSubmit={handleChangePwd}>
              <div className="form-group"><label>当前密码</label><input type="password" value={oldPwd} onChange={(e) => setOldPwd(e.target.value)} required /></div>
              <div className="form-group"><label>新密码</label><input type="password" value={newPwd} onChange={(e) => setNewPwd(e.target.value)} placeholder="至少6位" required minLength={6} /></div>
              <div className="form-group"><label>确认新密码</label><input type="password" value={confirmPwd} onChange={(e) => setConfirmPwd(e.target.value)} required /></div>
              <button type="submit" className="btn btn-primary" disabled={pwdLoading}>{pwdLoading ? "修改中..." : "确认修改"}</button>
            </form>
          </div>
        </div>
      </div>

      {moods.length > 0 && (
        <div className="card" style={{ marginTop: 24 }}>
          <div className="card-header"><h3>🌈 心情轨迹</h3></div>
          <div className="card-body">
            <div className="mood-timeline">
              {moods.map((m) => (
                <div key={m.id} className="mood-timeline-item">
                  <span className="mood-tl-emoji">{m.emoji}</span>
                  <div className="mood-tl-content">
                    <span className="mood-tl-label">{m.mood}</span>
                    {m.note && <p className="mood-tl-note">{m.note}</p>}
                    <span className="mood-tl-time">{formatDate(m.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
