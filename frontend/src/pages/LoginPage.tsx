import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiLogin, ApiError } from "../api/client";
import { useAuth } from "../contexts/AuthContext";

export default function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await apiLogin({ identifier, password });
      await login(res.access_token);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-logo">🌸</span>
          <h1>EchoMie</h1>
          <p className="auth-tagline">让每一刻都温柔以待</p>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>用户名 / 邮箱</label>
            <input type="text" value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="输入用户名或邮箱" required autoFocus />
          </div>
          <div className="form-group">
            <label>密码</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="输入密码" required />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>{loading ? "登录中..." : "进入 EchoMie 🌸"}</button>
        </form>
        <div className="auth-footer">
          <Link to="/forgot-password">忘记密码？</Link>
          <span className="divider">·</span>
          <Link to="/register">注册新账号</Link>
        </div>
      </div>
    </div>
  );
}
