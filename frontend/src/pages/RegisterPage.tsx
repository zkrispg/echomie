import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiRegister, ApiError } from "../api/client";
import { useAuth } from "../contexts/AuthContext";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirmPwd) { setError("两次密码不一致"); return; }
    if (password.length < 6) { setError("密码至少6位"); return; }
    setLoading(true);
    try {
      const res = await apiRegister(username, email, password);
      await login(res.access_token);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "注册失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-logo">🌸</span>
          <h1>加入 EchoMie</h1>
          <p className="auth-tagline">开启你的治愈之旅</p>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group"><label>用户名</label><input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="至少2个字符" required minLength={2} autoFocus /></div>
          <div className="form-group"><label>邮箱</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com" required /></div>
          <div className="form-group"><label>密码</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="至少6位" required minLength={6} /></div>
          <div className="form-group"><label>确认密码</label><input type="password" value={confirmPwd} onChange={(e) => setConfirmPwd(e.target.value)} placeholder="再次输入密码" required /></div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>{loading ? "注册中..." : "开始治愈之旅 🌈"}</button>
        </form>
        <div className="auth-footer"><Link to="/login">已有账号？去登录</Link></div>
      </div>
    </div>
  );
}
