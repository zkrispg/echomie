import { View, Text, Textarea } from "@tarojs/components";
import Taro, { useDidShow } from "@tarojs/taro";
import { useState, useRef, useEffect } from "react";
import { apiChat, apiGetChatHistory, apiClearChatHistory, hasToken } from "../../api/client";
import "./index.scss";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const GREETING = "你好呀，我是 EchoMie 治愈小助手 🌸\n有什么想说的，都可以告诉我～";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: GREETING },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollId = useRef("msg-0");

  useDidShow(() => {
    if (!hasToken()) {
      Taro.redirectTo({ url: "/pages/login/index" });
      return;
    }
    apiGetChatHistory()
      .then((res) => {
        if (res.items.length > 0) {
          const history = res.items.map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
          }));
          setMessages([{ role: "assistant", content: GREETING }, ...history]);
        }
      })
      .catch(() => {});
  });

  useEffect(() => {
    scrollId.current = `msg-${messages.length - 1}`;
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await apiChat(text);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "抱歉，暂时无法回应，但我一直在这里陪着你 🌸" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    Taro.showModal({
      title: "提示",
      content: "确定清空所有聊天记录吗？",
      success(res) {
        if (res.confirm) {
          apiClearChatHistory()
            .then(() => setMessages([{ role: "assistant", content: GREETING }]))
            .catch(() => {});
        }
      },
    });
  };

  return (
    <View className="page-wrap chat-page">
      <View className="chat-header-bar">
        <Text className="chat-header-title">💬 AI 治愈陪伴</Text>
        {messages.length > 1 && (
          <Text className="chat-clear" onClick={handleClear}>🗑️</Text>
        )}
      </View>

      <scroll-view
        className="chat-messages"
        scrollY
        scrollIntoView={scrollId.current}
        scrollWithAnimation
      >
        {messages.map((msg, i) => (
          <View key={i} id={`msg-${i}`} className={`chat-bubble ${msg.role}`}>
            {msg.role === "assistant" && (
              <Text className="bubble-avatar">🌸</Text>
            )}
            <View className="bubble-content">
              <Text>{msg.content}</Text>
            </View>
          </View>
        ))}
        {loading && (
          <View className="chat-bubble assistant">
            <Text className="bubble-avatar">🌸</Text>
            <View className="bubble-content typing">
              <View className="dot" />
              <View className="dot" />
              <View className="dot" />
            </View>
          </View>
        )}
      </scroll-view>

      <View className="chat-input-bar">
        <Textarea
          className="chat-input"
          placeholder="说点什么吧…"
          value={input}
          onInput={(e) => setInput(e.detail.value)}
          onConfirm={handleSend}
          confirmType="send"
          autoHeight
          maxlength={500}
        />
        <View
          className={`chat-send-btn${!input.trim() || loading ? " disabled" : ""}`}
          onClick={handleSend}
        >
          <Text>发送</Text>
        </View>
      </View>
    </View>
  );
}
