import { View, Text, Input } from "@tarojs/components";
import Taro, { useDidShow } from "@tarojs/taro";
import { useState } from "react";
import { apiGetMe, apiUpdateAvatar, apiChangePassword, apiGetMoods, clearToken, hasToken, ApiError } from "../../api/client";
import type { UserMe, MoodItem } from "../../api/types";
import "./index.scss";

const AVATARS = ["🌸", "🦋", "🌈", "🧸", "🐱", "🐶", "🌻", "🍀", "🦊", "🐰", "🌙", "⭐", "🎀", "🍓", "🌺", "💜"];

export default function ProfilePage() {
  const [user, setUser] = useState<UserMe | null>(null);
  const [showPicker, setShowPicker] = useState(false);
  const [moods, setMoods] = useState<MoodItem[]>([]);
  const [oldPwd, setOldPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [pwdError, setPwdError] = useState("");
  const [pwdSuccess, setPwdSuccess] = useState("");

  useDidShow(() => {
    if (!hasToken()) { Taro.redirectTo({ url: "/pages/login/index" }); return; }
    apiGetMe().then(setUser).catch(() => {});
    apiGetMoods(20).then((r) => setMoods(r.items)).catch(() => {});
  });

  const handleAvatar = async (emoji: string) => {
    try {
      await apiUpdateAvatar(emoji);
      setUser((u) => u ? { ...u, avatar_emoji: emoji } : u);
      setShowPicker(false);
    } catch {}
  };

  const handleChangePwd = async () => {
    setPwdError(""); setPwdSuccess("");
    if (newPwd !== confirmPwd) { setPwdError("两次密码不一致"); return; }
    if (newPwd.length < 6) { setPwdError("新密码至少6位"); return; }
    try {
      await apiChangePassword({ old_password: oldPwd, new_password: newPwd });
      setPwdSuccess("密码修改成功");
      setOldPwd(""); setNewPwd(""); setConfirmPwd("");
    } catch (err) {
      setPwdError(err instanceof ApiError ? err.message : "修改失败");
    }
  };

  const handleLogout = () => {
    clearToken();
    Taro.redirectTo({ url: "/pages/login/index" });
  };

  return (
    <View className="page-wrap profile-page">
      <View className="profile-header">
        <View className="avatar-circle" onClick={() => setShowPicker(!showPicker)}>
          <Text className="avatar-text">{user?.avatar_emoji || "🌸"}</Text>
        </View>
        {showPicker && (
          <View className="avatar-picker">
            {AVATARS.map((e) => (
              <Text key={e} className={`avatar-opt${user?.avatar_emoji === e ? " active" : ""}`} onClick={() => handleAvatar(e)}>{e}</Text>
            ))}
          </View>
        )}
        <Text className="profile-name">{user?.username || ""}</Text>
        <Text className="profile-email">{user?.email || ""}</Text>
      </View>

      <View className="card" style={{ marginBottom: "28rpx" }}>
        <View className="card-header"><Text style={{ fontWeight: "700" }}>🔒 修改密码</Text></View>
        <View className="card-body">
          {pwdError && <View className="alert alert-error"><Text>{pwdError}</Text></View>}
          {pwdSuccess && <View className="alert alert-success"><Text>{pwdSuccess}</Text></View>}
          <View className="form-group">
            <Text className="form-label">当前密码</Text>
            <Input className="form-input" type="text" password value={oldPwd} onInput={(e) => setOldPwd(e.detail.value)} />
          </View>
          <View className="form-group">
            <Text className="form-label">新密码</Text>
            <Input className="form-input" type="text" password value={newPwd} onInput={(e) => setNewPwd(e.detail.value)} placeholder="至少6位" />
          </View>
          <View className="form-group">
            <Text className="form-label">确认新密码</Text>
            <Input className="form-input" type="text" password value={confirmPwd} onInput={(e) => setConfirmPwd(e.detail.value)} />
          </View>
          <View className="btn btn-primary btn-block" onClick={handleChangePwd}>
            <Text style={{ color: "#fff" }}>确认修改</Text>
          </View>
        </View>
      </View>

      {moods.length > 0 && (
        <View className="card" style={{ marginBottom: "28rpx" }}>
          <View className="card-header"><Text style={{ fontWeight: "700" }}>🌈 心情轨迹</Text></View>
          <View className="card-body">
            {moods.map((m) => (
              <View key={m.id} className="mood-item">
                <Text className="mood-item-emoji">{m.emoji}</Text>
                <View className="mood-item-body">
                  <Text className="mood-item-label">{m.mood}</Text>
                  <Text className="mood-item-time">{new Date(m.created_at).toLocaleString("zh-CN")}</Text>
                </View>
              </View>
            ))}
          </View>
        </View>
      )}

      <View className="btn btn-ghost btn-block" onClick={handleLogout}>
        <Text>退出登录</Text>
      </View>
    </View>
  );
}
