import { View, Text, Button } from "@tarojs/components";
import Taro from "@tarojs/taro";
import { useState } from "react";
import { apiWxLogin, setToken } from "../../api/client";
import "./index.scss";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    setLoading(true);
    setError("");
    try {
      const { code } = await Taro.login();
      const res = await apiWxLogin(code);
      setToken(res.access_token);
      Taro.switchTab({ url: "/pages/index/index" });
    } catch (e: any) {
      setError(e.message || "登录失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View className="login-page">
      <View className="login-card">
        <Text className="login-logo">🌸</Text>
        <Text className="login-title">EchoMie</Text>
        <Text className="login-subtitle">用 AI 治愈每一个瞬间</Text>
        {error && <View className="alert alert-error"><Text>{error}</Text></View>}
        <Button
          className="login-btn"
          onClick={handleLogin}
          loading={loading}
          disabled={loading}
        >
          {loading ? "登录中..." : "微信一键登录"}
        </Button>
      </View>
    </View>
  );
}
