import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiForgotCode, apiResetByCode, ApiError } from "../api/client";

type Step = "email" | "code";

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const navigate = useNavigate();

  const startCooldown = (seconds: number) => {
    setCooldown(seconds);
    const timer = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleSendCode = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await apiForgotCode(email);
      if (res.ok) {
        setStep("code");
        setSuccess("验证码已发送到邮箱，请查收");
        startCooldown(res.cooldown_seconds);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "发送失败");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0) return;
    setError("");
    setLoading(true);
    try {
      const res = await apiForgotCode(email);
      if (res.ok) {
        setSuccess("验证码已重新发送");
        startCooldown(res.cooldown_seconds);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "发送失败");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (newPassword !== confirmPwd) {
      setError("两次密码不一致");
      return;
    }
    if (newPassword.length < 6) {
      setError("密码至少6位");
      return;
    }

    setLoading(true);
    try {
      await apiResetByCode(email, code, newPassword);
      setSuccess("密码重置成功！正在跳转登录...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "重置失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-logo">🔑</span>
          <h1>重置密码</h1>
          <p>{step === "email" ? "输入注册邮箱接收验证码" : "输入验证码和新密码"}</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {step === "email" ? (
          <form onSubmit={handleSendCode} className="auth-form">
            <div className="form-group">
              <label>邮箱地址</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                autoFocus
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading}
            >
              {loading ? "发送中..." : "发送验证码"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleReset} className="auth-form">
            <div className="form-group">
              <label>邮箱</label>
              <input type="email" value={email} disabled />
            </div>
            <div className="form-group">
              <label>
                验证码
                <button
                  type="button"
                  className="btn-link"
                  onClick={handleResend}
                  disabled={cooldown > 0 || loading}
                  style={{ marginLeft: 8, fontSize: 13 }}
                >
                  {cooldown > 0 ? `${cooldown}s 后重发` : "重新发送"}
                </button>
              </label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="6位数字验证码"
                required
                maxLength={6}
                autoFocus
              />
            </div>
            <div className="form-group">
              <label>新密码</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="至少6位"
                required
                minLength={6}
              />
            </div>
            <div className="form-group">
              <label>确认新密码</label>
              <input
                type="password"
                value={confirmPwd}
                onChange={(e) => setConfirmPwd(e.target.value)}
                placeholder="再次输入新密码"
                required
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading}
            >
              {loading ? "重置中..." : "重置密码"}
            </button>
          </form>
        )}

        <div className="auth-footer">
          <Link to="/login">返回登录</Link>
        </div>
      </div>
    </div>
  );
}
