"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from "recharts";
import {
  Thermometer, Volume2, Zap, Sun, Wind,
  Music, RefreshCw, Wifi, AlertTriangle, CheckCircle, Clock
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ── Storage helpers ────────────────────────────────────────────────────────
function save(key: string, value: any) {
  try { localStorage.setItem(`sh_${key}`, JSON.stringify(value)); } catch {}
}
function load<T>(key: string, def: T): T {
  try {
    const v = localStorage.getItem(`sh_${key}`);
    return v ? JSON.parse(v) : def;
  } catch { return def; }
}

// ── Types ──────────────────────────────────────────────────────────────────
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
  outside_noise_source?: string;
  outside_noise_db?: number;
  outside_noise_desc?: string;
  outside_noise_impact?: string;
  comfort_suggestions?: { action: string; impact: string; expected_score_gain: number }[];
}

// ── Helpers ────────────────────────────────────────────────────────────────
function comfortColor(s: number) {
  return s >= 70 ? "text-green-400" : s >= 45 ? "text-yellow-400" : "text-red-400";
}
function comfortLabel(s: number) {
  return s >= 70 ? "Comfortable" : s >= 45 ? "Moderate" : s >= 25 ? "Warm — AC recommended" : "Uncomfortable";
}

const ROOMS: Record<string, string> = {
  bedroom: "🛏 Bedroom", living_room: "🛋 Living Room",
  kitchen: "🍳 Kitchen", office: "💻 Office",
};

const ALL_LANGUAGES = [
  "Hindi","Hinglish","English","Bengali","Telugu","Marathi","Tamil",
  "Gujarati","Kannada","Odia","Malayalam","Punjabi","Assamese",
  "Maithili","Sanskrit","Urdu","Kashmiri","Konkani","Sindhi",
  "Dogri","Manipuri","Bodo","Nepali",
];

// ── Sub-components ─────────────────────────────────────────────────────────
function StatCard({ icon, label, value, unit, active }: any) {
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

function MicrophoneMonitor() {
  const [listening, setListening] = useState(false);
  const [db,        setDb]        = useState<number | null>(null);
  const [label,     setLabel]     = useState("");
  const [error,     setError]     = useState("");
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef   = useRef<MediaStream | null>(null);
  const timerRef    = useRef<NodeJS.Timeout | null>(null);

  const start = async () => {
    try {
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx      = new AudioContext();
      const source   = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      setListening(true);
      setError("");
      timerRef.current = setInterval(() => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        const avg  = data.reduce((a, b) => a + b, 0) / data.length;
        const val  = Math.round(avg * 0.6 + 20);
        setDb(val);
        setLabel(val < 30 ? "Quiet" : val < 50 ? "Normal" : val < 65 ? "Moderate" : val < 80 ? "Loud" : "Very Loud");
      }, 500);
    } catch { setError("Microphone access denied."); }
  };

  const stop = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    if (timerRef.current) clearInterval(timerRef.current);
    setListening(false); setDb(null); setLabel("");
  };

  useEffect(() => () => stop(), []);

  return (
    <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Volume2 size={14} className="text-blue-400"/>
          <span className="text-sm font-medium text-gray-300">Live Microphone</span>
        </div>
        <button onClick={listening ? stop : start}
          className={`px-3 py-1 rounded-lg text-xs font-medium ${
            listening ? "bg-red-600 text-white" : "bg-green-600 text-white"
          }`}>
          {listening ? "Stop" : "Start"}
        </button>
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      {listening && db !== null && (
        <div className="flex items-center gap-3 mt-2">
          <p className={`text-2xl font-bold ${db > 65 ? "text-red-400" : db > 45 ? "text-yellow-400" : "text-green-400"}`}>
            {db} dB
          </p>
          <div className="flex-1">
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${
                db > 65 ? "bg-red-500" : db > 45 ? "bg-yellow-500" : "bg-green-500"
              }`} style={{ width: `${Math.min(100, db)}%` }}/>
            </div>
            <p className="text-xs text-gray-400 mt-1">{label}</p>
          </div>
        </div>
      )}
      {!listening && !error && (
        <p className="text-xs text-gray-500 mt-1">Live noise from laptop microphone</p>
      )}
    </div>
  );
}

function SmartEnergyCalculator() {
  const [categories,       setCategories]       = useState<any>(null);
  const [selectedDevices,  setSelectedDevices]  = useState<any[]>([]);
  const [result,           setResult]           = useState<any>(null);
  const [loading,          setLoading]          = useState(false);
  const [rate,             setRate]             = useState(6.0);

  useEffect(() => {
    fetch(`${API_BASE}/smart-devices/categories`)
      .then(r => r.json()).then(setCategories).catch(() => {});
  }, []);

  const addDevice = (catKey: string, devKey: string, dev: any) => {
    setSelectedDevices(prev => [...prev, {
      category: catKey, device_key: devKey, label: dev.label,
      ask: dev.ask, options: dev.options, quantity: 1, hours: 8,
      option: dev.options ? Object.keys(dev.options)[0] : null, is_on: true,
    }]);
  };

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/smart-devices/calculate-bill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          devices: selectedDevices.map(d => ({
            category: d.category, device_key: d.device_key,
            quantity: d.quantity, hours: d.hours,
            option: d.option, is_on: d.is_on,
          })),
          electricity_rate: rate,
        }),
      });
      setResult(await res.json());
    } finally { setLoading(false); }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-gray-400">₹</span>
        <input type="number" value={rate}
          onChange={e => setRate(Number(e.target.value))}
          className="w-20 bg-gray-800 rounded px-2 py-1 text-sm text-white"/>
        <span className="text-sm text-gray-400">per unit</span>
      </div>

      {categories && (
        <div className="mb-4 space-y-2">
          <p className="text-sm text-gray-400">Add devices (no need to know watts!):</p>
          {Object.entries(categories).map(([catKey, cat]: [string, any]) => (
            <details key={catKey} className="bg-gray-800/60 border border-gray-700/40 rounded-xl">
              <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-300">{cat.label}</summary>
              <div className="px-4 pb-3 flex flex-wrap gap-2">
                {Object.entries(cat.devices).map(([devKey, dev]: [string, any]) => (
                  <button key={devKey} onClick={() => addDevice(catKey, devKey, dev)}
                    className="px-3 py-1.5 bg-gray-700 hover:bg-blue-700 text-xs rounded-lg text-gray-300">
                    + {dev.label}
                  </button>
                ))}
              </div>
            </details>
          ))}
        </div>
      )}

      {selectedDevices.length > 0 && (
        <div className="mb-4 space-y-2">
          <p className="text-sm text-gray-400">Your devices:</p>
          {selectedDevices.map((d, idx) => (
            <div key={idx} className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-3">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium text-white flex-1">{d.label}</span>
                {d.ask === "tons" && d.options && (
                  <select value={d.option || ""}
                    onChange={e => { const u=[...selectedDevices]; u[idx]={...d,option:e.target.value}; setSelectedDevices(u); }}
                    className="bg-gray-700 text-white text-xs rounded px-2 py-1">
                    {Object.keys(d.options).map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                )}
                {d.ask === "wattage" && d.options && (
                  <select value={d.option || ""}
                    onChange={e => { const u=[...selectedDevices]; u[idx]={...d,option:e.target.value}; setSelectedDevices(u); }}
                    className="bg-gray-700 text-white text-xs rounded px-2 py-1">
                    {Object.keys(d.options).map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                )}
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-400">Qty:</span>
                  <input type="number" value={d.quantity} min={1} max={20}
                    onChange={e => { const u=[...selectedDevices]; u[idx]={...d,quantity:Number(e.target.value)}; setSelectedDevices(u); }}
                    className="w-12 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-400">Hrs/day:</span>
                  <input type="number" value={d.hours} min={0} max={24} step={0.5}
                    onChange={e => { const u=[...selectedDevices]; u[idx]={...d,hours:Number(e.target.value)}; setSelectedDevices(u); }}
                    className="w-16 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
                </div>
                <button onClick={() => setSelectedDevices(prev => prev.filter((_,i) => i!==idx))}
                  className="text-red-400 text-xs px-2">✕</button>
              </div>
            </div>
          ))}

          <button onClick={calculate} disabled={loading}
            className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium">
            {loading ? "Calculating..." : "Calculate Bill & Get AI Suggestions"}
          </button>
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">Current Monthly Bill</p>
              <p className="text-3xl font-bold text-red-400">₹{result.monthly_bill}</p>
              <p className="text-xs text-gray-400 mt-1">₹{result.daily_cost}/day</p>
            </div>
            <div className="bg-green-900/20 border border-green-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">After AI Suggestions</p>
              <p className="text-3xl font-bold text-green-400">₹{result.optimized_bill}</p>
              <p className="text-xs text-green-300 mt-1">Save ₹{result.monthly_saving}/month</p>
            </div>
          </div>

          {result.suggestions?.length > 0 && (
            <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-4">
              <p className="text-sm font-medium text-yellow-300 mb-2 flex items-center gap-2">
                <CheckCircle size={14}/> AI Suggestions
              </p>
              {result.suggestions.map((s: any, i: number) => (
                <div key={i} className="text-sm mb-2 pb-2 border-b border-gray-700/30 last:border-0">
                  <p className="text-white font-medium">{s.device}</p>
                  <p className="text-gray-300 text-xs">{s.suggestion}</p>
                  <p className="text-green-400 text-xs">Save ₹{s.saving}/day → ₹{Math.round(s.saving*30)}/month</p>
                </div>
              ))}
            </div>
          )}

          <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
            <p className="text-sm font-medium mb-2">Cost breakdown (highest first)</p>
            {result.breakdown?.map((d: any, i: number) => (
              <div key={i} className="flex justify-between text-sm py-1 border-b border-gray-700/30 last:border-0">
                <span className="text-gray-300">{d.device} × {d.hours}h</span>
                <span><span className="text-white font-medium">₹{d.cost}</span><span className="text-gray-400">/day</span></span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────
export default function Dashboard() {
  const [snapshot,      setSnapshot]      = useState<Record<string, RoomState>>({});
  const [selectedRoom,  setSelectedRoom]  = useState(() => load("selectedRoom", "bedroom"));
  const [history,       setHistory]       = useState<any[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [lastUpdated,   setLastUpdated]   = useState("");
  const [backendError,  setBackendError]  = useState("");
  const [activeTab,     setActiveTab]     = useState
    "environment"|"devices"|"health"|"emotion"|"sleep"|"energy"|"chat"
  >(() => load("activeTab", "environment") as any);

  const [healthForm,    setHealthForm]    = useState(() => load("healthForm", {
    temperature_c: 26, noise_db: 40, light_level: 20,
    sleep_hour: 23, wake_hour: 7, health_conditions: [] as string[],
  }));
  const [healthResult,  setHealthResult]  = useState<any>(null);

  const [emotionText,   setEmotionText]   = useState("");
  const [emotionResult, setEmotionResult] = useState<any>(null);
  const [emotionLoading,setEmotionLoading]= useState(false);

  const [weatherPlace,  setWeatherPlace]  = useState(() => load("weatherPlace", ""));
  const [weatherResult, setWeatherResult] = useState<any>(null);
  const [weatherLoading,setWeatherLoading]= useState(false);

  const [chatMessages,  setChatMessages]  = useState<{role:string,content:string}[]>(
    () => load("chatMessages", [])
  );
  const [chatInput,     setChatInput]     = useState("");
  const [chatLanguage,  setChatLanguage]  = useState(() => load("chatLanguage", "Hindi"));
  const [chatLoading,   setChatLoading]   = useState(false);

  // Persist state
  useEffect(() => save("selectedRoom",  selectedRoom),  [selectedRoom]);
  useEffect(() => save("activeTab",     activeTab),     [activeTab]);
  useEffect(() => save("healthForm",    healthForm),    [healthForm]);
  useEffect(() => save("weatherPlace",  weatherPlace),  [weatherPlace]);
  useEffect(() => save("chatMessages",  chatMessages),  [chatMessages]);
  useEffect(() => save("chatLanguage",  chatLanguage),  [chatLanguage]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setBackendError("");
    try {
      const res  = await fetch(`${API_BASE}/environment/snapshot`);
      if (!res.ok) throw new Error(`Backend error ${res.status}`);
      const snap = await res.json();
      setSnapshot(snap);
      setLastUpdated(new Date().toLocaleTimeString());

      try {
        const hist = await fetch(`${API_BASE}/environment/history/${selectedRoom}?limit=15`);
        const hdata= await hist.json();
        if (hdata.history) setHistory([...hdata.history].reverse());
      } catch {}
    } catch (e: any) {
      setBackendError(e.message || "Cannot reach backend");
    } finally {
      setLoading(false);
    }
  }, [selectedRoom]);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    const t = setInterval(refresh, 30000);
    return () => clearInterval(t);
  }, [refresh]);

  const analyzeEmotion = async () => {
    if (!emotionText.trim()) return;
    setEmotionLoading(true);
    try {
      const res  = await fetch(`${API_BASE}/emotion/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: emotionText, user_id: "dashboard_user" }),
      });
      setEmotionResult(await res.json());
    } catch {
      setEmotionResult({ error: "Could not analyze — backend may be sleeping. Try again." });
    } finally { setEmotionLoading(false); }
  };

  const analyzeHealth = async () => {
    try {
      const res  = await fetch(`${API_BASE}/sleep/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(healthForm),
      });
      setHealthResult(await res.json());
    } catch { setHealthResult({ error: "Backend error" }); }
  };

  const getWeather = async (placeName?: string) => {
    const name = placeName || weatherPlace;
    if (!name.trim()) return;
    setWeatherLoading(true);
    try {
      const res  = await fetch(`${API_BASE}/weather/place?name=${encodeURIComponent(name)}`);
      setWeatherResult(await res.json());
    } catch { setWeatherResult({ error: "Weather fetch failed" }); }
    finally { setWeatherLoading(false); }
  };

  const getGPSWeather = () => {
    if (!navigator.geolocation) { alert("GPS not available"); return; }
    setWeatherLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const res  = await fetch(
            `${API_BASE}/weather/gps?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`
          );
          setWeatherResult(await res.json());
        } finally { setWeatherLoading(false); }
      },
      () => { alert("GPS access denied"); setWeatherLoading(false); },
      { timeout: 10000 }
    );
  };

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userMsg   = { role: "user", content: chatInput };
    const newMsgs   = [...chatMessages, userMsg];
    setChatMessages(newMsgs);
    setChatInput("");
    setChatLoading(true);
    try {
      const room = snapshot[selectedRoom];
      const res  = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages:        newMsgs,
          language:        chatLanguage,
          user_emotion:    emotionResult?.detected_emotion,
          room_conditions: room ? {
            temperature: room.temperature_c,
            noise: room.noise_db,
            comfort: room.comfort_score,
          } : null,
          user_id: "dashboard_user",
        }),
      });
      const data = await res.json();
      setChatMessages([...newMsgs, { role: "assistant", content: data.reply }]);
    } catch {
      setChatMessages([...newMsgs, { role: "assistant", content: "Sorry, could not connect. Try again." }]);
    } finally { setChatLoading(false); }
  };

  const room = snapshot[selectedRoom];

  const TABS = [
    { id: "environment", label: "🏠 Environment" },
    { id: "devices",     label: "⚡ Device Timer" },
    { id: "health",      label: "❤️ Health" },
    { id: "emotion",     label: "😊 Emotion" },
    { id: "sleep",       label: "🌙 Sleep & Weather" },
    { id: "energy",      label: "💡 Energy" },
    { id: "chat",        label: "💬 Talk to AI" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4 max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">SmartHome AI</h1>
          <p className="text-sm text-gray-400">Intelligence System · All Phases Complete</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{lastUpdated}</span>
          <button onClick={refresh}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-sm px-3 py-2 rounded-lg">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""}/>
            Refresh
          </button>
        </div>
      </div>

      {/* Backend error banner */}
      {backendError && (
        <div className="bg-red-900/30 border border-red-700/40 rounded-xl p-3 mb-4 text-sm text-red-300">
          ⚠️ Backend: {backendError}. Render free tier sleeps after 15 min — wait 30-60 seconds and refresh.
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {TABS.map(tab => (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.id
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── ENVIRONMENT ─────────────────────────────────────────────────── */}
      {activeTab === "environment" && (
        <div>
          <div className="flex gap-2 mb-4 flex-wrap">
            {Object.keys(ROOMS).map(r => {
              const s = snapshot[r];
              return (
                <button key={r} onClick={() => setSelectedRoom(r)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium ${
                    selectedRoom === r ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400"
                  }`}>
                  {ROOMS[r]}
                  {s && <span className={`ml-2 text-xs font-bold ${comfortColor(s.comfort_score)}`}>{s.comfort_score}</span>}
                </button>
              );
            })}
          </div>

          {loading && !room && (
            <div className="text-center py-12 text-gray-500">
              <RefreshCw size={24} className="animate-spin mx-auto mb-2"/>
              Loading room data...
              {backendError && (
                <p className="text-xs text-red-400 mt-2">
                  Backend sleeping — takes 30-60 seconds on free tier. Please wait.
                </p>
              )}
            </div>
          )}

          {room && (
            <>
              {/* Comfort score */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 mb-4 flex justify-between items-center">
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
                  <p className="text-sm text-gray-400">{ROOMS[selectedRoom]}</p>
                  <div className="flex items-center gap-2 mt-1 justify-end">
                    <Wifi size={12} className="text-green-400"/>
                    <span className="text-xs text-green-400">Live</span>
                  </div>
                  <p className="text-xs text-gray-500">{new Date().toLocaleTimeString()}</p>
                </div>
              </div>

              {/* Outside noise */}
              {room.outside_noise_source && (
                <div className={`rounded-xl p-4 mb-4 border ${
                  (room.outside_noise_db||0) > 70
                    ? "bg-red-900/20 border-red-700/40"
                    : "bg-gray-800/60 border-gray-700/40"
                }`}>
                  <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                    <Volume2 size={12}/> Outside Noise Detection
                  </p>
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-white capitalize">
                        {room.outside_noise_source.replace(/_/g," ")}
                      </p>
                      <p className="text-xs text-gray-400">{room.outside_noise_desc}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${
                        (room.outside_noise_db||0)>75?"text-red-400":
                        (room.outside_noise_db||0)>55?"text-yellow-400":"text-green-400"
                      }`}>{room.outside_noise_db?.toFixed(1)} dB</p>
                      <p className="text-xs text-gray-400">{room.outside_noise_impact}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Comfort suggestions */}
              {room.comfort_score < 60 && room.comfort_suggestions && room.comfort_suggestions.length > 0 && (
                <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-4 mb-4">
                  <p className="text-sm font-medium text-yellow-300 mb-2 flex items-center gap-2">
                    <AlertTriangle size={14}/> AI Comfort Suggestions
                  </p>
                  {room.comfort_suggestions.map((s, i) => (
                    <div key={i} className="text-sm flex justify-between py-1">
                      <span className="text-gray-300">• {s.action}</span>
                      <span className="text-green-400">+{s.expected_score_gain} pts</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Stats grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                <StatCard icon={<Thermometer size={18}/>} label="Temperature" value={room.temperature_c} unit="°C"/>
                <StatCard icon={<Volume2 size={18}/>} label="Indoor Noise" value={room.noise_db} unit="dB"/>
                <StatCard icon={<Zap size={18}/>} label="Power Usage" value={room.power_watts} unit="W"/>
                <StatCard icon={<Sun size={18}/>} label="Light Level" value={room.light_level} unit="%"/>
                <StatCard icon={<Wind size={18}/>} label="AC / Fan"
                  value={room.ac_on?"AC On":room.fan_on?"Fan On":"Off"}
                  active={room.ac_on||room.fan_on}/>
                <StatCard icon={<Music size={18}/>} label="Music"
                  value={room.music_playing?"Playing":"Off"}
                  active={room.music_playing}/>
              </div>

              {/* Live microphone */}
              <div className="mb-4"><MicrophoneMonitor/></div>

              {/* History chart */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5">
                <p className="text-sm font-medium text-gray-300 mb-4">Comfort History (real time)</p>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
                    <XAxis dataKey="timestamp" tick={{ fontSize: 9, fill: "#9CA3AF" }}
                      tickFormatter={v => new Date(v).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}/>
                    <YAxis domain={[0,100]} tick={{ fontSize: 9, fill: "#9CA3AF" }}/>
                    <Tooltip
                      contentStyle={{ background:"#1F2937", border:"1px solid #374151", borderRadius:"8px", fontSize:"12px" }}
                      labelFormatter={l => new Date(l).toLocaleTimeString()}/>
                    <Line type="monotone" dataKey="comfort_score" stroke="#60A5FA" strokeWidth={2} dot={false}/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── DEVICE TIMER ────────────────────────────────────────────────── */}
      {activeTab === "devices" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Smart Device Timer & Bill Calculator</h2>
          <p className="text-sm text-gray-400 mb-4">
            Add devices, set hours — see your monthly bill and AI saving suggestions instantly.
            No need to know watts!
          </p>
          <SmartEnergyCalculator/>
        </div>
      )}

      {/* ── HEALTH ──────────────────────────────────────────────────────── */}
      {activeTab === "health" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Health & Sleep Analysis</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            {[
              {label:"Room Temp (°C)", key:"temperature_c", min:10, max:45},
              {label:"Noise (dB)",     key:"noise_db",      min:0,  max:100},
              {label:"Light Level (%)",key:"light_level",   min:0,  max:100},
              {label:"Sleep Hour",     key:"sleep_hour",    min:18, max:26},
              {label:"Wake Hour",      key:"wake_hour",     min:4,  max:12},
            ].map(f => (
              <div key={f.key}>
                <label className="text-xs text-gray-400 mb-1 block">{f.label}</label>
                <input type="number" value={(healthForm as any)[f.key]}
                  min={f.min} max={f.max}
                  onChange={e => setHealthForm({...healthForm, [f.key]: Number(e.target.value)})}
                  className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
              </div>
            ))}
          </div>

          <div className="mb-4">
            <label className="text-xs text-gray-400 mb-2 block">Health Conditions:</label>
            <div className="flex flex-wrap gap-2">
              {["high_bp","low_bp","high_sugar","low_sugar","diabetes",
                "anxiety","insomnia","asthma","migraine","arthritis",
                "high_heart_rate","tachycardia","low_heart_rate","bradycardia",
                "low_haemoglobin","anaemia","high_haemoglobin",
                "thyroid_hypo","thyroid_hyper","pcod"].map(c => (
                <button key={c}
                  onClick={() => {
                    const cs = healthForm.health_conditions;
                    setHealthForm({...healthForm,
                      health_conditions: cs.includes(c) ? cs.filter(x=>x!==c) : [...cs,c]
                    });
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    healthForm.health_conditions.includes(c)
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-gray-400"
                  }`}>
                  {c.replace(/_/g," ")}
                </button>
              ))}
            </div>
          </div>

          <button onClick={analyzeHealth}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium mb-4">
            Analyze Now
          </button>

          {healthResult && !healthResult.error && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4 text-center">
                <p className={`text-4xl font-bold ${comfortColor(healthResult.sleep_score)}`}>
                  {healthResult.sleep_score}/100
                </p>
                <p className={`text-sm mt-1 ${comfortColor(healthResult.sleep_score)}`}>
                  {healthResult.quality}
                </p>
              </div>

              {healthResult.health_tips?.length > 0 && (
                <div className="space-y-2">
                  {healthResult.health_tips.map((tip: any, i: number) => (
                    <div key={i} className="bg-blue-900/20 border border-blue-700/40 rounded-xl p-4">
                      <p className="text-sm font-medium text-white mb-1">{tip.condition}</p>
                      <p className="text-xs text-gray-400 mb-2">{tip.tip}</p>
                      <p className="text-xs text-blue-400">Suggested: {tip.suggested_temp}°C, {tip.suggested_noise}dB</p>
                      {tip.gharelu_upay?.length > 0 && (
                        <div className="mt-2 p-2 bg-green-900/20 rounded border border-green-700/30">
                          <p className="text-xs font-medium text-green-400 mb-1">🌿 घरेलू उपाय:</p>
                          {tip.gharelu_upay.map((u: string, j: number) => (
                            <p key={j} className="text-xs text-gray-300">• {u}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {healthResult.recommendations?.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-sm font-medium mb-2">Recommendations</p>
                  {healthResult.recommendations.map((r: any, i: number) => (
                    <div key={i} className="text-sm py-1 border-b border-gray-700/30 last:border-0">
                      <span className="text-gray-400">{r.issue}: </span>
                      <span className="text-white">{r.action}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── EMOTION ─────────────────────────────────────────────────────── */}
      {activeTab === "emotion" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Emotion Detection</h2>
          <p className="text-sm text-gray-400 mb-4">
            Type in any Indian language — system detects emotion and suggests environment changes.
            Note: On Render free tier first analysis may take 30-60 seconds.
          </p>
          <textarea value={emotionText} onChange={e => setEmotionText(e.target.value)}
            placeholder="How are you feeling? Type in Hindi, English, Tamil, or any Indian language..."
            className="w-full bg-gray-800 rounded-xl px-4 py-3 text-white text-sm h-24 resize-none mb-3"/>
          <button onClick={analyzeEmotion} disabled={emotionLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-xl font-medium mb-4">
            {emotionLoading ? "Analyzing... (may take 30-60s on first request)" : "Detect Emotion"}
          </button>

          {emotionResult?.error && (
            <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4">
              <p className="text-red-400 text-sm">{emotionResult.error}</p>
            </div>
          )}

          {emotionResult && !emotionResult.error && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-2xl font-bold text-white capitalize">{emotionResult.detected_emotion}</p>
                    <p className="text-xs text-gray-400">
                      {emotionResult.confidence}% confidence · {emotionResult.language_detected}
                      {emotionResult.detection_source && ` · ${emotionResult.detection_source}`}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    emotionResult.auto_act ? "bg-green-900/40 text-green-400" : "bg-yellow-900/40 text-yellow-400"
                  }`}>
                    {emotionResult.auto_act ? "Auto-adjusting" : "Suggestion"}
                  </span>
                </div>
                <p className="text-sm text-gray-300">{emotionResult.explanation}</p>
              </div>

              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <p className="text-sm font-medium mb-2">Environment Adjustment</p>
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

      {/* ── SLEEP & WEATHER ─────────────────────────────────────────────── */}
      {activeTab === "sleep" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Sleep & Weather</h2>

          <div className="flex gap-2 mb-2">
            <input value={weatherPlace} onChange={e => setWeatherPlace(e.target.value)}
              onKeyDown={e => e.key === "Enter" && getWeather()}
              placeholder="Any city, village, colony, cantt, district..."
              className="flex-1 bg-gray-800 rounded-xl px-4 py-3 text-white text-sm"/>
            <button onClick={() => getWeather()} disabled={weatherLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-3 rounded-xl text-sm font-medium">
              {weatherLoading ? "..." : "Search"}
            </button>
            <button onClick={getGPSWeather} disabled={weatherLoading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-3 rounded-xl text-sm"
              title="Use my current GPS location">
              📍
            </button>
          </div>

          <p className="text-xs text-gray-500 mb-4">
            Works for any place worldwide — colonies, villages, cantonments, districts.
            Examples: "Ambala Cantt", "Koramangala Bangalore", "Dharavi Mumbai", "Kasol Himachal"
          </p>

          {weatherResult && !weatherResult.error && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <p className="font-medium text-white">
                  {weatherResult.location?.name}
                  {weatherResult.location?.city && weatherResult.location?.city !== weatherResult.location?.name
                    && `, ${weatherResult.location.city}`}
                </p>
                {weatherResult.location?.full && (
                  <p className="text-xs text-gray-400">{weatherResult.location.full}</p>
                )}
                {weatherResult.location?.detected_by && (
                  <p className="text-xs text-green-400">📍 {weatherResult.location.detected_by}</p>
                )}
                <p className="text-sm text-gray-400 mt-1">{weatherResult.outdoor?.condition}</p>

                <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                  <p className="text-gray-400">Temp: <span className="text-white">{weatherResult.outdoor?.temperature_c}°C</span></p>
                  <p className="text-gray-400">Feels: <span className="text-white">{weatherResult.outdoor?.feels_like_c}°C</span></p>
                  <p className="text-gray-400">Humidity: <span className="text-white">{weatherResult.outdoor?.humidity_percent}%</span></p>
                  <p className="text-gray-400">Wind: <span className="text-white">{weatherResult.outdoor?.wind_speed_kmh} km/h {weatherResult.outdoor?.wind_direction}</span></p>
                  <p className="text-gray-400">Indoor est: <span className="text-white">{weatherResult.indoor_estimate?.temperature_c}°C</span></p>
                  <p className="text-gray-400">UV Index: <span className="text-white">{weatherResult.outdoor?.uv_index}</span></p>
                </div>

                {/* Alternative locations */}
                {weatherResult.other_matches?.length > 0 && (
                  <div className="mt-3 p-2 bg-yellow-900/20 border border-yellow-700/30 rounded-lg">
                    <p className="text-xs text-yellow-400 mb-1">Other matching places:</p>
                    {weatherResult.other_matches.map((m: any, i: number) => (
                      <button key={i}
                        onClick={async () => {
                          setWeatherLoading(true);
                          const res = await fetch(`${API_BASE}/weather/by-coordinates?lat=${m.lat}&lon=${m.lon}&name=${encodeURIComponent(m.name)}`);
                          setWeatherResult(await res.json());
                          setWeatherLoading(false);
                        }}
                        className="block text-xs text-blue-400 hover:text-blue-300 py-0.5">
                        → {m.display || m.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className={`rounded-xl p-4 border ${
                (weatherResult.sleep_impact?.sleep_weather_score||0) >= 75
                  ? "bg-green-900/20 border-green-700/40"
                  : "bg-yellow-900/20 border-yellow-700/40"
              }`}>
                <p className="text-sm font-medium">Sleep Score: {weatherResult.sleep_impact?.sleep_weather_score}/100</p>
                <p className="text-sm text-gray-300">{weatherResult.sleep_impact?.overall}</p>
                {weatherResult.sleep_impact?.impacts?.map((imp: string, i: number) => (
                  <p key={i} className="text-xs text-gray-400 mt-1">• {imp}</p>
                ))}
              </div>

              {weatherResult.recommendations?.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-sm font-medium mb-2">Recommendations</p>
                  {weatherResult.recommendations.map((r: string, i: number) => (
                    <p key={i} className="text-xs text-gray-300 py-1">• {r}</p>
                  ))}
                </div>
              )}

              {weatherResult.forecast_3day?.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-sm font-medium mb-3">3-Day Forecast</p>
                  <div className="grid grid-cols-3 gap-2">
                    {weatherResult.forecast_3day.map((day: any, i: number) => (
                      <div key={i} className="text-center p-2 bg-gray-700/40 rounded-lg">
                        <p className="text-xs text-gray-400">
                          {new Date(day.date).toLocaleDateString("en-IN",{weekday:"short"})}
                        </p>
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

      {/* ── ENERGY ──────────────────────────────────────────────────────── */}
      {activeTab === "energy" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Energy Optimizer</h2>
          <p className="text-sm text-gray-400 mb-4">
            Advanced monthly bill prediction using XGBoost AI model.
          </p>
          <EnergyOptimizer apiBase={API_BASE}/>
        </div>
      )}

      {/* ── CHAT ────────────────────────────────────────────────────────── */}
      {activeTab === "chat" && (
        <div className="flex flex-col" style={{height:"75vh"}}>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-semibold flex-1">Talk to your Smart Home</h2>
            <select value={chatLanguage} onChange={e => setChatLanguage(e.target.value)}
              className="bg-gray-800 text-white text-sm rounded-lg px-3 py-2 border border-gray-700">
              {ALL_LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
            {chatMessages.length > 0 && (
              <button onClick={() => setChatMessages([])}
                className="text-xs text-gray-500 hover:text-gray-300">Clear</button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1 min-h-0">
            {chatMessages.length === 0 && (
              <div className="text-center py-8">
                <p className="text-4xl mb-3">💬</p>
                <p className="text-gray-400 text-sm">Talk to your home in {chatLanguage}</p>
                <p className="text-gray-500 text-xs mt-1">All 22 Indian languages supported</p>
                <div className="flex flex-wrap gap-2 justify-center mt-4">
                  {[
                    "Mera room kaisa hai?",
                    "Sleep tips batao",
                    "Bijli bill kaise kam karo",
                    "Main bahut stressed hoon",
                    "Aaj ka mausam kaisa hai",
                    "AC kitne time chalana chahiye",
                  ].map(s => (
                    <button key={s} onClick={() => setChatInput(s)}
                      className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-full text-xs text-gray-300">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatMessages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role==="user"?"justify-end":"justify-start"}`}>
                <div className={`max-w-xs md:max-w-md rounded-2xl px-4 py-3 text-sm ${
                  msg.role==="user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-gray-800 text-gray-100 rounded-bl-sm"
                }`}>{msg.content}</div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3">
                  <div className="flex gap-1">
                    {[0,0.1,0.2].map((d,i) => (
                      <div key={i} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{animationDelay:`${d}s`}}/>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <input value={chatInput} onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key==="Enter" && sendChat()}
              placeholder={`Type in ${chatLanguage}... (Enter to send)`}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white text-sm"/>
            <button onClick={sendChat} disabled={chatLoading || !chatInput.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-3 rounded-xl text-sm font-medium">
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Energy Optimizer component ─────────────────────────────────────────────
function EnergyOptimizer({ apiBase }: { apiBase: string }) {
  const [devices,  setDevices]  = useState([
    { name: "AC 1.5ton", daily_hours: 8,  wattage: 1500, quantity: 1 },
    { name: "Fan",       daily_hours: 12, wattage: 75,   quantity: 3 },
    { name: "LED Bulb",  daily_hours: 6,  wattage: 9,    quantity: 6 },
    { name: "Fridge",    daily_hours: 24, wattage: 150,  quantity: 1 },
  ]);
  const [result, setResult] = useState<any>(null);
  const [loading,setLoading] = useState(false);
  const [rate,   setRate]   = useState(6.0);

  const predict = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/energy/predict/monthly`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ devices, electricity_rate_per_unit: rate }),
      });
      setResult(await res.json());
    } catch { setResult({ error: "Backend error" }); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-gray-400">Rate: ₹</span>
        <input type="number" value={rate} onChange={e => setRate(Number(e.target.value))}
          className="w-20 bg-gray-800 rounded px-2 py-1 text-sm text-white" step={0.5}/>
        <span className="text-sm text-gray-400">/unit</span>
      </div>

      <div className="space-y-2 mb-4">
        {devices.map((d, idx) => (
          <div key={idx} className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-white min-w-28">{d.name}</span>
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-400">Qty:</span>
                <input type="number" value={d.quantity} min={1} max={20}
                  onChange={e => { const u=[...devices]; u[idx]={...d,quantity:Number(e.target.value)}; setDevices(u); }}
                  className="w-12 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
              </div>
              <div className="flex items-center gap-1">
                <Clock size={12} className="text-gray-400"/>
                <input type="number" value={d.daily_hours} min={0} max={24} step={0.5}
                  onChange={e => { const u=[...devices]; u[idx]={...d,daily_hours:Number(e.target.value)}; setDevices(u); }}
                  className="w-16 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
                <span className="text-xs text-gray-400">h/day</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button onClick={predict} disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-xl font-medium mb-4">
        {loading ? "Predicting..." : "Predict Monthly Bill with AI"}
      </button>

      {result && !result.error && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">Current Bill</p>
              <p className="text-3xl font-bold text-red-400">₹{result.predicted_monthly_bill}</p>
            </div>
            <div className="bg-green-900/20 border border-green-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">After Optimization</p>
              <p className="text-3xl font-bold text-green-400">₹{result.optimized_bill}</p>
              <p className="text-xs text-green-300">Save ₹{result.potential_saving}/month</p>
            </div>
          </div>

          {result.optimization_tips?.map((tip: string, i: number) => (
            <div key={i} className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-3">
              <p className="text-sm text-gray-300">• {tip}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
