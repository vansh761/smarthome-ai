"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchSnapshot, fetchRoomHistory } from "@/lib/api";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from "recharts";
import {
  Thermometer, Volume2, Zap, Sun, Wind,
  Music, RefreshCw, Wifi, Activity,
  AlertTriangle, CheckCircle, Clock
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface RoomState {
  room:                  string;
  temperature_c:         number;
  humidity_percent:      number;
  light_level:           number;
  light_color:           string;
  noise_db:              number;
  music_playing:         boolean;
  power_watts:           number;
  ac_on:                 boolean;
  fan_on:                boolean;
  comfort_score:         number;
  timestamp:             string;
  outside_noise_source?: string;
  outside_noise_db?:     number;
  outside_noise_desc?:   string;
  outside_noise_impact?: string;
}

interface HistoryEntry {
  timestamp:     string;
  temperature_c: number;
  noise_db:      number;
  comfort_score: number;
  power_watts:   number;
}

interface TimerDevice {
  name:     string;
  watts:    number;
  quantity: number;
  hours:    number;
  is_on:    boolean;
}

function comfortColor(score: number) {
  if (score >= 70) return "text-green-400";
  if (score >= 45) return "text-yellow-400";
  return "text-red-400";
}

function comfortLabel(score: number) {
  if (score >= 70) return "Comfortable";
  if (score >= 45) return "Moderate";
  if (score >= 25) return "Warm — AC recommended";
  return "Uncomfortable";
}

const ROOM_LABELS: Record<string, string> = {
  bedroom:     "🛏 Bedroom",
  living_room: "🛋 Living Room",
  kitchen:     "🍳 Kitchen",
  office:      "💻 Office",
};

function StatCard({ icon, label, value, unit, active }: {
  icon: React.ReactNode; label: string;
  value: string | number; unit?: string; active?: boolean;
}) {
  return (
    <div className={`rounded-xl p-4 flex items-center gap-3 ${
      active ? "bg-blue-900/40 border border-blue-700/50" : "bg-gray-800/60 border border-gray-700/40"
    }`}>
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

export default function Dashboard() {
  const [snapshot,      setSnapshot]      = useState<Record<string, RoomState>>({});
  const [selectedRoom,  setSelectedRoom]  = useState("bedroom");
  const [history,       setHistory]       = useState<HistoryEntry[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [lastUpdated,   setLastUpdated]   = useState("");
  const [activeTab,     setActiveTab]     = useState<"environment"|"devices"|"health"|"emotion"|"sleep"|"energy">("environment");

  // Device timer state
  const [timerDevices,  setTimerDevices]  = useState<TimerDevice[]>([
    { name: "Ceiling Fan", watts: 75,   quantity: 1, hours: 8,  is_on: true },
    { name: "AC 1.5ton",   watts: 1500, quantity: 1, hours: 8,  is_on: false },
    { name: "LED Bulb",    watts: 9,    quantity: 4, hours: 6,  is_on: true },
    { name: "Refrigerator",watts: 150,  quantity: 1, hours: 24, is_on: true },
  ]);
  const [timerResult,   setTimerResult]   = useState<any>(null);
  const [timerLoading,  setTimerLoading]  = useState(false);

  // Health state
  const [healthForm,    setHealthForm]    = useState({
    temperature_c: 26, noise_db: 40, light_level: 20,
    sleep_hour: 23, wake_hour: 7,
    health_conditions: [] as string[],
  });
  const [healthResult,  setHealthResult]  = useState<any>(null);

  // Emotion state
  const [emotionText,   setEmotionText]   = useState("");
  const [emotionResult, setEmotionResult] = useState<any>(null);
  const [emotionLoading,setEmotionLoading]= useState(false);

  // Weather state
  const [weatherPlace,  setWeatherPlace]  = useState("Delhi");
  const [weatherResult, setWeatherResult] = useState<any>(null);

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
    const run = async () => { if (!cancelled) await refresh(); };
    run();
    return () => { cancelled = true; };
  }, [refresh]);

  useEffect(() => {
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const runTimer = async () => {
    setTimerLoading(true);
    try {
      const res = await fetch(`${API_BASE}/device-timer/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          devices: timerDevices,
          electricity_rate: 6.0,
        }),
      });
      const data = await res.json();
      setTimerResult(data);
    } finally {
      setTimerLoading(false);
    }
  };

  const analyzeHealth = async () => {
    const res = await fetch(`${API_BASE}/sleep/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(healthForm),
    });
    const data = await res.json();
    setHealthResult(data);
  };

  const analyzeEmotion = async () => {
    if (!emotionText.trim()) return;
    setEmotionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/emotion/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: emotionText, user_id: "dashboard_user" }),
      });
      const data = await res.json();
      setEmotionResult(data);
    } finally {
      setEmotionLoading(false);
    }
  };

  const getWeather = async () => {
    const res = await fetch(`${API_BASE}/weather/place?name=${encodeURIComponent(weatherPlace)}`);
    const data = await res.json();
    setWeatherResult(data);
  };

  const room = snapshot[selectedRoom];

  const tabs = [
    { id: "environment", label: "🏠 Environment" },
    { id: "devices",     label: "⚡ Device Timer" },
    { id: "health",      label: "❤️ Health" },
    { id: "emotion",     label: "😊 Emotion" },
    { id: "sleep",       label: "🌙 Sleep" },
    { id: "energy",      label: "💡 Weather" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">SmartHome AI</h1>
          <p className="text-sm text-gray-400">Intelligence System · All Features</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">Updated {lastUpdated}</span>
          <button onClick={refresh}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-sm px-3 py-2 rounded-lg">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {tabs.map(tab => (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.id
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── ENVIRONMENT TAB ─────────────────────────────────────────────── */}
      {activeTab === "environment" && (
        <div>
          {/* Room selector */}
          <div className="flex gap-3 mb-6 flex-wrap">
            {Object.keys(ROOM_LABELS).map(r => {
              const s = snapshot[r];
              return (
                <button key={r} onClick={() => setSelectedRoom(r)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    selectedRoom === r ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}>
                  {ROOM_LABELS[r]}
                  {s && <span className={`ml-2 text-xs font-bold ${comfortColor(s.comfort_score)}`}>{s.comfort_score}</span>}
                </button>
              );
            })}
          </div>

          {room ? (
            <>
              {/* Comfort banner */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 mb-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Comfort Score</p>
                  <p className={`text-5xl font-bold ${comfortColor(room.comfort_score)}`}>
                    {room.comfort_score}<span className="text-xl text-gray-400">/100</span>
                  </p>
                  <p className={`text-sm mt-1 ${comfortColor(room.comfort_score)}`}>
                    {comfortLabel(room.comfort_score)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-400">{ROOM_LABELS[selectedRoom]}</p>
                  <div className="flex items-center gap-2 mt-2 justify-end">
                    <Wifi size={14} className="text-green-400" />
                    <span className="text-xs text-green-400">Live</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date().toLocaleTimeString()}
                  </p>
                </div>
              </div>

              {/* Outside noise panel */}
              {room.outside_noise_source && (
                <div className={`rounded-xl p-4 mb-4 border ${
                  (room.outside_noise_db || 0) > 70
                    ? "bg-red-900/20 border-red-700/40"
                    : "bg-gray-800/60 border-gray-700/40"
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Volume2 size={16} className="text-yellow-400" />
                    <span className="text-sm font-medium text-gray-300">Outside Noise Detection</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-semibold text-white capitalize">
                        {room.outside_noise_source?.replace(/_/g, " ")}
                      </p>
                      <p className="text-xs text-gray-400">{room.outside_noise_desc}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${
                        (room.outside_noise_db || 0) > 75 ? "text-red-400" :
                        (room.outside_noise_db || 0) > 55 ? "text-yellow-400" : "text-green-400"
                      }`}>{room.outside_noise_db?.toFixed(1)} dB</p>
                      <p className="text-xs text-gray-400">{room.outside_noise_impact}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                <StatCard icon={<Thermometer size={18}/>} label="Temperature" value={room.temperature_c} unit="°C"/>
                <StatCard icon={<Volume2 size={18}/>} label="Indoor Noise" value={room.noise_db} unit="dB"/>
                <StatCard icon={<Zap size={18}/>} label="Power Usage" value={room.power_watts} unit="W"/>
                <StatCard icon={<Sun size={18}/>} label="Light Level" value={room.light_level} unit="%"/>
                <StatCard icon={<Wind size={18}/>} label="AC / Fan"
                  value={room.ac_on ? "AC On" : room.fan_on ? "Fan On" : "Off"}
                  active={room.ac_on || room.fan_on}/>
                <StatCard icon={<Music size={18}/>} label="Music"
                  value={room.music_playing ? "Playing" : "Off"}
                  active={room.music_playing}/>
              </div>

              {/* Auto-fix suggestion */}
              {room.comfort_score < 50 && (
                <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-4 mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle size={16} className="text-yellow-400"/>
                    <span className="text-sm font-medium text-yellow-300">AI Comfort Suggestions</span>
                  </div>
                  <div className="space-y-1 text-sm text-gray-300">
                    {room.temperature_c > 26 && <p>• Lower temperature — turn on AC or fan</p>}
                    {room.noise_db > 50 && <p>• Room is noisy — close windows</p>}
                    {(room.outside_noise_db || 0) > 70 && <p>• High outside noise — close windows immediately</p>}
                    {room.light_level > 70 && <p>• Reduce light level for better comfort</p>}
                  </div>
                </div>
              )}

              {/* History chart with real time */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5">
                <h2 className="text-sm font-medium text-gray-300 mb-4">
                  Comfort Score — last {history.length} readings (real time)
                </h2>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
                    <XAxis dataKey="timestamp" tick={{ fontSize: 10, fill: "#9CA3AF" }}
                      tickFormatter={(v) => new Date(v).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}/>
                    <YAxis domain={[0,100]} tick={{ fontSize: 10, fill: "#9CA3AF" }}/>
                    <Tooltip
                      contentStyle={{ background: "#1F2937", border: "1px solid #374151", borderRadius: "8px", fontSize: "12px" }}
                      <Tooltip
                        contentStyle={{
                          background: "#1F2937",
                          border: "1px solid #374151",
                        }}
                        formatter={(v) => [`${v ?? 0}`, "Comfort"]}
                        labelFormatter={(l) => new Date(l).toLocaleTimeString()}
                      />
                      labelFormatter={(l) => new Date(l).toLocaleTimeString()}/>
                    <Line type="monotone" dataKey="comfort_score" stroke="#60A5FA" strokeWidth={2} dot={false}/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">Loading room data...</div>
          )}
        </div>
      )}

      {/* ── DEVICE TIMER TAB ─────────────────────────────────────────────── */}
      {activeTab === "devices" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Device Timer & Bill Simulator</h2>
          <p className="text-sm text-gray-400 mb-4">
            Set devices and hours — see bill and AI suggestions instantly. No need to wait!
          </p>

          {/* Device list */}
          <div className="space-y-3 mb-4">
            {timerDevices.map((device, idx) => (
              <div key={idx} className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <button
                    onClick={() => {
                      const updated = [...timerDevices];
                      updated[idx] = { ...device, is_on: !device.is_on };
                      setTimerDevices(updated);
                    }}
                    className={`w-10 h-6 rounded-full transition-colors ${device.is_on ? "bg-green-500" : "bg-gray-600"}`}>
                    <div className={`w-4 h-4 bg-white rounded-full mx-1 transition-transform ${device.is_on ? "translate-x-4" : ""}`}/>
                  </button>
                  <span className="text-sm font-medium text-white min-w-32">{device.name}</span>
                  <span className="text-xs text-gray-400">{device.watts}W × {device.quantity}</span>
                  <div className="flex items-center gap-2 ml-auto">
                    <Clock size={14} className="text-gray-400"/>
                    <input
                      type="number"
                      value={device.hours}
                      onChange={(e) => {
                        const updated = [...timerDevices];
                        updated[idx] = { ...device, hours: Number(e.target.value) };
                        setTimerDevices(updated);
                      }}
                      className="w-20 bg-gray-700 rounded px-2 py-1 text-sm text-white"
                      min={0} max={24} step={0.5}
                    />
                    <span className="text-xs text-gray-400">hrs</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button onClick={runTimer} disabled={timerLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4">
            {timerLoading ? "Calculating..." : "Calculate Bill & Get AI Suggestions"}
          </button>

          {timerResult && (
            <div className="space-y-4">
              {/* Bill comparison */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-400 mb-1">Current Bill</p>
                  <p className="text-3xl font-bold text-red-400">₹{timerResult.simulation.current_cost}</p>
                  <p className="text-xs text-gray-400">for this session</p>
                  <p className="text-sm text-red-300 mt-1">₹{timerResult.monthly_projection.current_bill}/month</p>
                </div>
                <div className="bg-green-900/20 border border-green-700/40 rounded-xl p-4 text-center">
                  <p className="text-xs text-gray-400 mb-1">After AI Suggestions</p>
                  <p className="text-3xl font-bold text-green-400">₹{timerResult.simulation.optimized_cost}</p>
                  <p className="text-xs text-gray-400">for this session</p>
                  <p className="text-sm text-green-300 mt-1">₹{timerResult.monthly_projection.optimized_bill}/month</p>
                </div>
              </div>

              <div className="bg-blue-900/20 border border-blue-700/40 rounded-xl p-3 text-center">
                <p className="text-sm text-blue-300">{timerResult.verdict}</p>
              </div>

              {/* AI suggestions */}
              {timerResult.ai_suggestions.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-400"/>
                    AI Recommendations
                  </h3>
                  {timerResult.ai_suggestions.map((s: any, i: number) => (
                    <div key={i} className={`p-3 rounded-lg mb-2 ${
                      s.severity === "high" ? "bg-red-900/20 border border-red-700/30" : "bg-yellow-900/20 border border-yellow-700/30"
                    }`}>
                      <p className="text-sm font-medium text-white">{s.device}</p>
                      <p className="text-xs text-gray-400">{s.issue}</p>
                      <p className="text-xs text-green-400">✓ {s.recommendation}</p>
                      <p className="text-xs text-yellow-400">Save ₹{s.saving_rupees} this session</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Device breakdown */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <h3 className="text-sm font-medium mb-3">Device Breakdown</h3>
                {timerResult.device_breakdown.map((d: any, i: number) => (
                  <div key={i} className="flex justify-between text-sm py-1 border-b border-gray-700/40 last:border-0">
                    <span className="text-gray-300">{d.device}</span>
                    <span className="text-gray-400">{d.hours}h → <span className="text-white font-medium">₹{d.cost}</span></span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── HEALTH TAB ────────────────────────────────────────────────────── */}
      {activeTab === "health" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Health & Sleep Analysis</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Room Temp (°C)</label>
              <input type="number" value={healthForm.temperature_c}
                onChange={e => setHealthForm({...healthForm, temperature_c: Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Noise (dB)</label>
              <input type="number" value={healthForm.noise_db}
                onChange={e => setHealthForm({...healthForm, noise_db: Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Light Level (%)</label>
              <input type="number" value={healthForm.light_level}
                onChange={e => setHealthForm({...healthForm, light_level: Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Sleep Hour</label>
              <input type="number" value={healthForm.sleep_hour}
                onChange={e => setHealthForm({...healthForm, sleep_hour: Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Wake Hour</label>
              <input type="number" value={healthForm.wake_hour}
                onChange={e => setHealthForm({...healthForm, wake_hour: Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
          </div>

          <div className="mb-4">
            <label className="text-xs text-gray-400 mb-2 block">Health Conditions (select all that apply)</label>
            <div className="flex flex-wrap gap-2">
              {["high_bp","low_bp","high_sugar","low_sugar","anxiety",
                "insomnia","asthma","migraine","high_heart_rate","low_haemoglobin",
                "thyroid_hypo","thyroid_hyper","pcod","arthritis","diabetes"].map(c => (
                <button key={c}
                  onClick={() => {
                    const conds = healthForm.health_conditions;
                    setHealthForm({
                      ...healthForm,
                      health_conditions: conds.includes(c)
                        ? conds.filter(x => x !== c)
                        : [...conds, c]
                    });
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    healthForm.health_conditions.includes(c)
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}>
                  {c.replace(/_/g," ")}
                </button>
              ))}
            </div>
          </div>

          <button onClick={analyzeHealth}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4">
            Analyze Health & Sleep
          </button>

          {healthResult && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4 text-center">
                <p className="text-xs text-gray-400 mb-1">Sleep Quality Score</p>
                <p className={`text-4xl font-bold ${comfortColor(healthResult.sleep_score)}`}>
                  {healthResult.sleep_score}/100
                </p>
                <p className={`text-sm mt-1 ${comfortColor(healthResult.sleep_score)}`}>
                  {healthResult.quality}
                </p>
              </div>

              {healthResult.health_tips?.length > 0 && (
                <div className="bg-blue-900/20 border border-blue-700/40 rounded-xl p-4">
                  <h3 className="text-sm font-medium mb-2 text-blue-300">Health-Specific Tips</h3>
                  {healthResult.health_tips.map((tip: any, i: number) => (
                    <div key={i} className="mb-2 p-2 bg-gray-800/40 rounded-lg">
                      <p className="text-xs font-medium text-white">{tip.condition}</p>
                      <p className="text-xs text-gray-400">{tip.tip}</p>
                      <p className="text-xs text-blue-400">Suggested temp: {tip.suggested_temp}°C</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <h3 className="text-sm font-medium mb-2">Ideal Environment Tonight</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <p className="text-gray-400">Temperature: <span className="text-white">{healthResult.ideal_environment?.temperature_c}°C</span></p>
                  <p className="text-gray-400">Light: <span className="text-white">{healthResult.ideal_environment?.light_level}%</span></p>
                  <p className="text-gray-400">Sleep: <span className="text-white">{healthResult.ideal_environment?.recommended_sleep_time}</span></p>
                  <p className="text-gray-400">Wake: <span className="text-white">{healthResult.ideal_environment?.recommended_wake_time}</span></p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── EMOTION TAB ──────────────────────────────────────────────────── */}
      {activeTab === "emotion" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Emotion Detection</h2>
          <p className="text-sm text-gray-400 mb-4">
            Type how you feel in any Indian language — system detects emotion and adjusts environment.
          </p>
          <textarea
            value={emotionText}
            onChange={e => setEmotionText(e.target.value)}
            placeholder="How are you feeling? Type in Hindi, English, Tamil, Gujarati, or any Indian language..."
            className="w-full bg-gray-800 rounded-xl px-4 py-3 text-white text-sm mb-3 h-24 resize-none"
          />
          <button onClick={analyzeEmotion} disabled={emotionLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4">
            {emotionLoading ? "Analyzing..." : "Detect Emotion & Adjust Environment"}
          </button>

          {emotionResult && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <p className="text-2xl font-bold text-white capitalize">{emotionResult.detected_emotion}</p>
                    <p className="text-xs text-gray-400">{emotionResult.confidence}% confidence · {emotionResult.language_detected}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    emotionResult.auto_act ? "bg-green-900/40 text-green-400" : "bg-yellow-900/40 text-yellow-400"
                  }`}>
                    {emotionResult.auto_act ? "Auto-adjusting" : "Suggestion only"}
                  </span>
                </div>
                <p className="text-sm text-gray-300">{emotionResult.explanation}</p>
              </div>

              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <h3 className="text-sm font-medium mb-2">Environment Adjustment</h3>
                <p className="text-sm text-gray-300 mb-2">{emotionResult.environment_suggestion?.message}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <p className="text-gray-400">Temp: <span className="text-white">{emotionResult.environment_suggestion?.temperature_c}°C</span></p>
                  <p className="text-gray-400">Light: <span className="text-white">{emotionResult.environment_suggestion?.light_level}%</span></p>
                  <p className="text-gray-400">Color: <span className="text-white">{emotionResult.environment_suggestion?.light_color}</span></p>
                  <p className="text-gray-400">Music: <span className="text-white">{emotionResult.environment_suggestion?.music}</span></p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SLEEP/WEATHER TAB ────────────────────────────────────────────── */}
      {activeTab === "sleep" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Sleep & Weather Conditions</h2>
          <div className="flex gap-2 mb-4">
            <input
              value={weatherPlace}
              onChange={e => setWeatherPlace(e.target.value)}
              placeholder="Enter city, district, village, colony..."
              className="flex-1 bg-gray-800 rounded-xl px-4 py-3 text-white text-sm"
            />
            <button onClick={getWeather}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-xl text-sm font-medium">
              Get Weather
            </button>
          </div>

          {weatherResult && !weatherResult.error && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <h3 className="font-medium text-white mb-1">
                  {weatherResult.location?.name}, {weatherResult.location?.state}
                </h3>
                <p className="text-xs text-gray-400 mb-3">{weatherResult.outdoor?.condition}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <p className="text-gray-400">Outdoor: <span className="text-white">{weatherResult.outdoor?.temperature_c}°C</span></p>
                  <p className="text-gray-400">Feels: <span className="text-white">{weatherResult.outdoor?.feels_like_c}°C</span></p>
                  <p className="text-gray-400">Humidity: <span className="text-white">{weatherResult.outdoor?.humidity_percent}%</span></p>
                  <p className="text-gray-400">Wind: <span className="text-white">{weatherResult.outdoor?.wind_speed_kmh} km/h {weatherResult.outdoor?.wind_direction}</span></p>
                  <p className="text-gray-400">Indoor est: <span className="text-white">{weatherResult.indoor_estimate?.temperature_c}°C</span></p>
                  <p className="text-gray-400">UV Index: <span className="text-white">{weatherResult.outdoor?.uv_index}</span></p>
                </div>
              </div>

              <div className={`rounded-xl p-4 ${
                weatherResult.sleep_impact?.sleep_weather_score >= 75
                  ? "bg-green-900/20 border border-green-700/40"
                  : "bg-yellow-900/20 border border-yellow-700/40"
              }`}>
                <p className="text-sm font-medium mb-1">Sleep Weather Score: {weatherResult.sleep_impact?.sleep_weather_score}/100</p>
                <p className="text-sm text-gray-300">{weatherResult.sleep_impact?.overall}</p>
                {weatherResult.sleep_impact?.impacts?.map((imp: string, i: number) => (
                  <p key={i} className="text-xs text-gray-400 mt-1">• {imp}</p>
                ))}
              </div>

              {weatherResult.forecast_3day && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <h3 className="text-sm font-medium mb-3">3-Day Forecast</h3>
                  <div className="grid grid-cols-3 gap-2">
                    {weatherResult.forecast_3day.map((day: any, i: number) => (
                      <div key={i} className="text-center p-2 bg-gray-700/40 rounded-lg">
                        <p className="text-xs text-gray-400">{new Date(day.date).toLocaleDateString("en-IN", {weekday:"short"})}</p>
                        <p className="text-sm font-bold text-white">{day.max_temp}°</p>
                        <p className="text-xs text-gray-400">{day.min_temp}°</p>
                        {day.rain_probability > 0 && (
                          <p className="text-xs text-blue-400">{day.rain_probability}% rain</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {weatherResult?.error && (
            <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4">
              <p className="text-red-400 text-sm">{weatherResult.error}</p>
              {weatherResult.tip && <p className="text-gray-400 text-xs mt-1">{weatherResult.tip}</p>}
            </div>
          )}
        </div>
      )}

      {/* ── ENERGY TAB ────────────────────────────────────────────────────── */}
      {activeTab === "energy" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Energy & API Reference</h2>
          <p className="text-sm text-gray-400 mb-4">All system endpoints available for testing.</p>
          <div className="space-y-2">
            {[
              {method:"GET",  path:"/environment/snapshot",   desc:"Live sensor data all rooms"},
              {method:"POST", path:"/energy/predict/monthly", desc:"Monthly electricity bill prediction"},
              {method:"POST", path:"/sleep/predict",          desc:"Sleep quality score"},
              {method:"POST", path:"/emotion/analyze",        desc:"Emotion detection 23 languages"},
              {method:"POST", path:"/memory/analyze-and-remember", desc:"Emotion with memory"},
              {method:"POST", path:"/memory/predict",         desc:"Pattern-based prediction"},
              {method:"GET",  path:"/weather/place?name=Delhi", desc:"Real weather any location"},
              {method:"POST", path:"/device-timer/simulate",  desc:"Device timer bill calculator"},
              {method:"GET",  path:"/transparency/principles", desc:"Ethical AI principles"},
              {method:"GET",  path:"/evaluation/benchmark",   desc:"System benchmark"},
              {method:"GET",  path:"/mqtt/status",            desc:"MQTT hardware bridge status"},
              {method:"GET",  path:"/automation/modes",       desc:"Manual/Assisted/Full AI modes"},
            ].map((ep, i) => (
              <a key={i} href={`${API_BASE}${ep.path}`} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-3 bg-gray-800/60 border border-gray-700/40 rounded-xl p-3 hover:border-gray-500/60 transition-colors">
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                  ep.method === "GET" ? "bg-green-900/60 text-green-400" : "bg-blue-900/60 text-blue-400"
                }`}>{ep.method}</span>
                <span className="text-sm text-gray-300 font-mono flex-1">{ep.path}</span>
                <span className="text-xs text-gray-500 hidden md:block">{ep.desc}</span>
              </a>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
