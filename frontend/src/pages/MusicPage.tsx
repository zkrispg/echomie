import { useState, useEffect, useRef } from "react";
import { apiGetMusic } from "../api/client";
import type { MusicItem } from "../api/types";
import { EMOTION_MAP } from "../api/types";

const EMOTION_LIST = Object.entries(EMOTION_MAP).map(([key, v]) => ({
  key,
  ...v,
}));

export default function MusicPage() {
  const [tracks, setTracks] = useState<MusicItem[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [emotion, setEmotion] = useState("");
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    apiGetMusic(emotion)
      .then((res) => setTracks(res.items))
      .catch(() => {});
  }, [emotion]);

  const currentTrack = tracks.find((t) => t.id === currentId);

  const play = (track: MusicItem) => {
    if (currentId === track.id && isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
      return;
    }

    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audio = new Audio(track.url);
    audioRef.current = audio;
    setCurrentId(track.id);
    setProgress(0);
    setDuration(0);

    audio.addEventListener("loadedmetadata", () => setDuration(audio.duration));
    audio.addEventListener("timeupdate", () => setProgress(audio.currentTime));
    audio.addEventListener("ended", () => {
      setIsPlaying(false);
      const idx = tracks.findIndex((t) => t.id === track.id);
      if (idx < tracks.length - 1) {
        play(tracks[idx + 1]);
      }
    });

    audio.play().then(() => setIsPlaying(true)).catch(() => {});
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const t = Number(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = t;
      setProgress(t);
    }
  };

  const fmtTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const emotionInfo = (key: string) =>
    EMOTION_MAP[key] || { label: key, emoji: "🎵", color: "#ccc" };

  return (
    <div className="music-page">
      <div className="music-header">
        <span className="music-header-icon">🎵</span>
        <h2>音乐治愈</h2>
        <p className="music-subtitle">让音乐陪伴你的每一个瞬间</p>
      </div>

      <div className="emotion-filter">
        <button
          className={`emotion-chip${emotion === "" ? " active" : ""}`}
          onClick={() => setEmotion("")}
        >
          全部
        </button>
        {EMOTION_LIST.map((e) => (
          <button
            key={e.key}
            className={`emotion-chip${emotion === e.key ? " active" : ""}`}
            style={emotion === e.key ? { background: e.color + "33", borderColor: e.color } : undefined}
            onClick={() => setEmotion(e.key)}
          >
            {e.emoji} {e.label}
          </button>
        ))}
      </div>

      <div className="track-list">
        {tracks.map((track) => {
          const ei = emotionInfo(track.emotion);
          const active = currentId === track.id;
          return (
            <div
              key={track.id}
              className={`track-item${active ? " active" : ""}`}
              onClick={() => play(track)}
            >
              <div
                className="track-emotion-dot"
                style={{ background: ei.color }}
              />
              <div className="track-info">
                <span className="track-name">{track.name}</span>
                <span className="track-emotion-label">{ei.emoji} {ei.label}</span>
              </div>
              <span className="track-play-icon">
                {active && isPlaying ? "⏸" : "▶"}
              </span>
            </div>
          );
        })}
        {tracks.length === 0 && (
          <div className="empty-state">暂无音乐</div>
        )}
      </div>

      {currentTrack && (
        <div className="music-player-bar">
          <div className="player-info">
            <span className="player-name">{currentTrack.name}</span>
          </div>
          <div className="player-controls">
            <button className="player-btn" onClick={togglePlay}>
              {isPlaying ? "⏸" : "▶"}
            </button>
            <span className="player-time">{fmtTime(progress)}</span>
            <input
              type="range"
              className="player-progress"
              min={0}
              max={duration || 0}
              step={0.1}
              value={progress}
              onChange={seek}
            />
            <span className="player-time">{fmtTime(duration)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
