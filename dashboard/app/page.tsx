"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchSnapshot, fetchRoomHistory } from "@/lib/api";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from "recharts";
import {
  Thermometer, Volume2, Zap, Sun,
  Wind, Music, RefreshCw, Wifi
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────
interface RoomState {
  room: string;
  temperature_c: number;
  humidity_percent: number;
  light_level: number;
  light_color: string;
  noise_db: number;
  music_playing: boolean;
  power_watts: number;
  ac_on: boolean;
  fan_on: boolean;
  comfort_score: number;
  timestamp: string;
}

interface HistoryEntry {
  timestamp: string;
  temperature_c: number;
  noise_db: number;
  comfort_score: number;
  power_watts: number;
}

// ── Helpers ────────────────────────────────────────────────────
function comfortColor(score: number) {
  if (score >= 75) return "text-green-400";
  if (score >= 50) return "text-yellow-400";
  return "text-red-400";
}

function comfortLabel(score: number) {
  if (score >= 75) return "Comfortable";
  if (score >= 50) return "Moderate";
  return "Uncomfortable";
}

const ROOM_LABELS: Record<string, string> = {
  bedroom: "🛏 Bedroom",
  living_room: "🛋 Living Room",
  kitchen: "🍳 Kitchen",
  office: "💻 Office",
};

// ── Stat Card ──────────────────────────────────────────────────
function StatCard({
  icon, label, value, unit, active
}: {
  icon: React.ReactNode; label: string;
  value: string | number; unit?: string; active?: boolean;
}) {
  return (
    <div className={`rounded-xl p-4 flex items-center gap-3 
      ${active ? "bg-blue-900/40 border border-blue-700/50" : "bg-gray-800/60 border border-gray-700/40"}`}>
      <div className="text-gray-400">{icon}</div>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-lg font-semibold text-white">
          {value}<span className="text-sm text-gray-400 ml-1">{unit}</span>
        </p>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────
export default function Dashboard() {
  const [snapshot, setSnapshot] = useState<Record<string, RoomState>>({});
  const [selectedRoom, setSelectedRoom] = useState("bedroom");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");

 const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const snap = await fetchSnapshot();
      setSnapshot(snap);
      const hist = await fetchRoomHistory(selectedRoom, 15);
      setHistory(hist.history.reverse());
      setLastUpdated(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
    }
  }, [selectedRoom]);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!cancelled) await refresh();
    };
    run();
    return () => { cancelled = true; };
  }, [refresh]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const room = snapshot[selectedRoom];

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">SmartHome AI</h1>
          <p className="text-sm text-gray-400">
            Intelligence System · Phase 1
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            Updated {lastUpdated}
          </span>
          <button
            onClick={refresh}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 
                       text-sm px-3 py-2 rounded-lg transition-colors"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Room selector */}
      <div className="flex gap-3 mb-8 flex-wrap">
        {Object.keys(ROOM_LABELS).map((r) => {
          const s = snapshot[r];
          return (
            <button
              key={r}
              onClick={() => setSelectedRoom(r)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all
                ${selectedRoom === r
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
            >
              {ROOM_LABELS[r]}
              {s && (
                <span className={`ml-2 text-xs font-bold ${comfortColor(s.comfort_score)}`}>
                  {s.comfort_score}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {room ? (
        <>
          {/* Comfort Score Banner */}
          <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl 
                          p-5 mb-6 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-1">Comfort Score</p>
              <p className={`text-5xl font-bold ${comfortColor(room.comfort_score)}`}>
                {room.comfort_score}
                <span className="text-xl text-gray-400">/100</span>
              </p>
              <p className={`text-sm mt-1 ${comfortColor(room.comfort_score)}`}>
                {comfortLabel(room.comfort_score)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">
                {ROOM_LABELS[selectedRoom]}
              </p>
              <div className="flex items-center gap-2 mt-2 justify-end">
                <Wifi size={14} className="text-green-400" />
                <span className="text-xs text-green-400">Live</span>
              </div>
            </div>
          </div>

          {/* Stat Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
            <StatCard
              icon={<Thermometer size={18} />}
              label="Temperature"
              value={room.temperature_c}
              unit="°C"
            />
            <StatCard
              icon={<Volume2 size={18} />}
              label="Noise Level"
              value={room.noise_db}
              unit="dB"
            />
            <StatCard
              icon={<Zap size={18} />}
              label="Power Usage"
              value={room.power_watts}
              unit="W"
            />
            <StatCard
              icon={<Sun size={18} />}
              label="Light Level"
              value={room.light_level}
              unit="%"
            />
            <StatCard
              icon={<Wind size={18} />}
              label="AC / Fan"
              value={room.ac_on ? "AC On" : room.fan_on ? "Fan On" : "Off"}
              active={room.ac_on || room.fan_on}
            />
            <StatCard
              icon={<Music size={18} />}
              label="Music"
              value={room.music_playing ? "Playing" : "Off"}
              active={room.music_playing}
            />
          </div>

          {/* History Chart */}
          <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5">
            <h2 className="text-sm font-medium text-gray-300 mb-4">
              Comfort Score — last {history.length} readings
            </h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fontSize: 10, fill: "#9CA3AF" }}
                  tickFormatter={(v) =>
                    new Date(v).toLocaleTimeString([], {
                      hour: "2-digit", minute: "2-digit"
                    })
                  }
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 10, fill: "#9CA3AF" }}
                />
                <Tooltip
                  contentStyle={{
                    background: "#1F2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                    fontSize: "12px"
                  }}
                  formatter={(v) => [`${v ?? 0}`, "Comfort"]}
                  labelFormatter={(l) =>
                    new Date(l).toLocaleTimeString()
                  }
                />
                <Line
                  type="monotone"
                  dataKey="comfort_score"
                  stroke="#60A5FA"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : (
        <div className="flex items-center justify-center h-64 text-gray-500">
          Loading room data...
        </div>
      )}
    </div>
  );
}