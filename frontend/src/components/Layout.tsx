import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">🌸</span>
          <span className="brand-text">EchoMie</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end className="nav-item">
            <span className="nav-emoji">🏠</span>
            首页
          </NavLink>
          <NavLink to="/record" className="nav-item">
            <span className="nav-emoji">📷</span>
            记录此刻
          </NavLink>
          <NavLink to="/timeline" className="nav-item">
            <span className="nav-emoji">📖</span>
            情绪时间轴
          </NavLink>
          <NavLink to="/weekly" className="nav-item">
            <span className="nav-emoji">📊</span>
            每周总结
          </NavLink>
          <NavLink to="/tasks" className="nav-item">
            <span className="nav-emoji">📋</span>
            我的任务
          </NavLink>
          <NavLink to="/profile" className="nav-item">
            <span className="nav-emoji">💜</span>
            个人中心
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-badge">
            <div className="user-avatar-emoji">{user?.avatar_emoji || "🌸"}</div>
            <div className="user-info">
              <span className="user-name">{user?.username}</span>
            </div>
          </div>
          <button className="btn-logout" onClick={() => { logout(); navigate("/login"); }} title="退出">
            <span className="nav-emoji" style={{ fontSize: "1.1rem" }}>👋</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
