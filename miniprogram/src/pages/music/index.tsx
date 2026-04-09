import { View, Text, Slider } from "@tarojs/components";
import Taro, { useDidShow, useDidHide } from "@tarojs/taro";
import { useState, useRef } from "react";
import { apiGetMusic, hasToken } from "../../api/client";
import { EMOTION_MAP } from "../../api/types";
import type { MusicItem } from "../../api/types";
import "./index.scss";

const EMOTION_LIST = Object.entries(EMOTION_MAP).map(([key, v]) => ({ key, ...v }));

export default function MusicPage() {
  const [tracks, setTracks] = useState<MusicItem[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [emotion, setEmotion] = useState("");
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<Taro.InnerAudioContext | null>(null);

  useDidShow(() => {
    if (!hasToken()) {
      Taro.redirectTo({ url: "/pages/login/index" });
      return;
    }
    loadTracks(emotion);
  });

  useDidHide(() => {
    if (audioRef.current) {
      audioRef.current.stop();
      audioRef.current.destroy();
      audioRef.current = null;
    }
  });

  const loadTracks = (em: string) => {
    apiGetMusic(em).then((res) => setTracks(res.items)).catch(() => {});
  };

  const currentTrack = tracks.find((t) => t.id === currentId);

  const play = (track: MusicItem) => {
    if (currentId === track.id && isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
      return;
    }

    if (audioRef.current) {
      audioRef.current.stop();
      audioRef.current.destroy();
    }

    const audio = Taro.createInnerAudioContext();
    audio.src = track.url;
    audioRef.current = audio;
    setCurrentId(track.id);
    setProgress(0);
    setDuration(0);

    audio.onCanplay(() => setDuration(audio.duration));
    audio.onTimeUpdate(() => {
      setProgress(audio.currentTime);
      if (audio.duration > 0) setDuration(audio.duration);
    });
    audio.onEnded(() => {
      setIsPlaying(false);
      const idx = tracks.findIndex((t) => t.id === track.id);
      if (idx < tracks.length - 1) play(tracks[idx + 1]);
    });
    audio.onError(() => {
      Taro.showToast({ title: "播放失败", icon: "none" });
      setIsPlaying(false);
    });

    audio.play();
    setIsPlaying(true);
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const seek = (val: number) => {
    if (audioRef.current) {
      audioRef.current.seek(val);
      setProgress(val);
    }
  };

  const fmtTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const emotionInfo = (key: string) =>
    EMOTION_MAP[key] || { label: key, emoji: "🎵", color: "#ccc" };

  const handleFilterChange = (em: string) => {
    setEmotion(em);
    loadTracks(em);
  };

  return (
    <View className="page-wrap music-page">
      <View className="music-header">
        <Text className="music-icon">🎵</Text>
        <Text className="music-title">音乐治愈</Text>
        <Text className="music-subtitle">让音乐陪伴你的每一个瞬间</Text>
      </View>

      <scroll-view className="emotion-filter" scrollX>
        <View className="filter-inner">
          <Text
            className={`emotion-chip${emotion === "" ? " active" : ""}`}
            onClick={() => handleFilterChange("")}
          >全部</Text>
          {EMOTION_LIST.map((e) => (
            <Text
              key={e.key}
              className={`emotion-chip${emotion === e.key ? " active" : ""}`}
              style={emotion === e.key ? { background: `${e.color}33`, borderColor: e.color } : {}}
              onClick={() => handleFilterChange(e.key)}
            >{e.emoji} {e.label}</Text>
          ))}
        </View>
      </scroll-view>

      <View className="track-list">
        {tracks.map((track) => {
          const ei = emotionInfo(track.emotion);
          const active = currentId === track.id;
          return (
            <View
              key={track.id}
              className={`track-item${active ? " active" : ""}`}
              onClick={() => play(track)}
            >
              <View className="track-dot" style={{ background: ei.color }} />
              <View className="track-info">
                <Text className="track-name">{track.name}</Text>
                <Text className="track-emotion">{ei.emoji} {ei.label}</Text>
              </View>
              <Text className="track-play-icon">{active && isPlaying ? "⏸" : "▶"}</Text>
            </View>
          );
        })}
        {tracks.length === 0 && (
          <View className="empty-state"><Text style={{ color: "#a89bb5" }}>暂无音乐</Text></View>
        )}
      </View>

      {currentTrack && (
        <View className="player-bar">
          <Text className="player-name">{currentTrack.name}</Text>
          <View className="player-controls">
            <Text className="player-btn" onClick={togglePlay}>{isPlaying ? "⏸" : "▶"}</Text>
            <Text className="player-time">{fmtTime(progress)}</Text>
            <Slider
              className="player-slider"
              min={0}
              max={Math.floor(duration) || 1}
              step={1}
              value={Math.floor(progress)}
              activeColor="#9b7ecb"
              backgroundColor="#ece4da"
              blockSize={14}
              onChange={(e) => seek(e.detail.value)}
            />
            <Text className="player-time">{fmtTime(duration)}</Text>
          </View>
        </View>
      )}
    </View>
  );
}
