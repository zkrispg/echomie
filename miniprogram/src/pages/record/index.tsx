import { View, Text, Textarea, Image } from "@tarojs/components";
import Taro, { useDidShow } from "@tarojs/taro";
import { useState, useCallback, useEffect } from "react";
import { apiUpload, apiGetStyles, hasToken, ApiError } from "../../api/client";
import type { StyleInfo } from "../../api/types";
import "./index.scss";

export default function RecordPage() {
  const [filePath, setFilePath] = useState("");
  const [fileType, setFileType] = useState<"image" | "video">("image");
  const [context, setContext] = useState("");
  const [style, setStyle] = useState("none");
  const [styles, setStyles] = useState<StyleInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [taskId, setTaskId] = useState<number | null>(null);

  useDidShow(() => {
    if (!hasToken()) {
      Taro.redirectTo({ url: "/pages/login/index" });
      return;
    }
  });

  useEffect(() => {
    apiGetStyles().then((r) => setStyles(r.styles)).catch(() => {});
  }, []);

  const chooseImage = useCallback(() => {
    Taro.chooseImage({
      count: 1,
      sizeType: ["compressed"],
      sourceType: ["album", "camera"],
      success(res) {
        setFilePath(res.tempFilePaths[0]);
        setFileType("image");
        setError("");
      },
    });
  }, []);

  const chooseVideo = useCallback(() => {
    Taro.chooseVideo({
      sourceType: ["album", "camera"],
      maxDuration: 60,
      compressed: true,
      success(res) {
        setFilePath(res.tempFilePath);
        setFileType("video");
        setError("");
      },
    });
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!filePath) return;
    setError("");
    setUploading(true);
    try {
      const res = await apiUpload(filePath, context.trim(), style);
      setTaskId(res.data.task_id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "上传失败，请重试");
    } finally {
      setUploading(false);
    }
  }, [filePath, context, style]);

  const resetFlow = useCallback(() => {
    setTaskId(null);
    setFilePath("");
    setContext("");
    setStyle("none");
    setError("");
  }, []);

  if (taskId !== null) {
    return (
      <View className="page-wrap record-page">
        <View className="success-card">
          <Text className="success-lead">已收到你的画面</Text>
          <Text className="task-id">任务编号 #{taskId}</Text>
          <View
            className="btn btn-primary btn-block btn-lg"
            onClick={() => Taro.navigateTo({ url: `/pages/card/index?taskId=${taskId}` })}
          >
            <Text style={{ color: "#fff" }}>查看疗愈回应</Text>
          </View>
          <View className="btn btn-ghost btn-block" style={{ marginTop: "20rpx" }} onClick={resetFlow}>
            <Text>再传一张</Text>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View className="page-wrap record-page">
      <Text className="page-title">记录这一刻</Text>
      <Text className="page-subtitle">上传画面，让 AI 感受并回应你</Text>

      {error && <View className="alert alert-error"><Text>{error}</Text></View>}

      {filePath ? (
        <View className="preview-card">
          {fileType === "image" ? (
            <Image className="preview-img" src={filePath} mode="aspectFill" />
          ) : (
            <View className="preview-video-placeholder"><Text>🎬 已选择视频</Text></View>
          )}
          <View className="preview-actions">
            <Text className="btn-remove" onClick={resetFlow}>移除</Text>
          </View>
        </View>
      ) : (
        <View className="upload-area">
          <View className="upload-btn" onClick={chooseImage}>
            <Text className="upload-icon">📷</Text>
            <Text>选择图片</Text>
          </View>
          <View className="upload-btn" onClick={chooseVideo}>
            <Text className="upload-icon">🎬</Text>
            <Text>选择视频</Text>
          </View>
        </View>
      )}

      <Textarea
        className="context-input"
        value={context}
        onInput={(e) => setContext(e.detail.value)}
        placeholder="可以告诉我画面里的小故事哦（选填）"
        maxlength={500}
        disabled={uploading}
      />

      {styles.length > 0 && (
        <View className="style-section">
          <Text className="style-title">选择卡通风格（选填）</Text>
          <View className="style-grid">
            {styles.map((s) => (
              <View
                key={s.key}
                className={`style-card${style === s.key ? " active" : ""}`}
                onClick={() => setStyle(s.key)}
              >
                <Text className="style-emoji">{s.emoji}</Text>
                <Text className="style-label">{s.label}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {uploading && <Text className="loading-text">AI 正在感受你的画面...</Text>}

      <View
        className={`submit-btn${!filePath || uploading ? " disabled" : ""}`}
        onClick={!filePath || uploading ? undefined : handleSubmit}
      >
        <Text style={{ color: "#fff" }}>让 AI 感受这一刻</Text>
      </View>
    </View>
  );
}
