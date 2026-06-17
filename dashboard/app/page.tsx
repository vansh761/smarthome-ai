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
const USER_ID  = "dashboard_user";

function save(key: string, value: any) {
  try { localStorage.setItem(`sh_${key}`, JSON.stringify(value)); } catch {}
}
function load<T>(key: string, def: T): T {
  try {
    const v = localStorage.getItem(`sh_${key}`);
    return v ? JSON.parse(v) : def;
  } catch { return def; }
}

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

function StatCard({ icon, label, value, unit, active, sub }: any) {
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
        {sub && <p className="text-xs text-gray-500">{sub}</p>}
      </div>
    </div>
  );
}

// Microphone hook — shared across components
function useMicrophone() {
  const [db,       setDb]       = useState<number | null>(null);
  const [active,   setActive]   = useState(false);
  const [error,    setError]    = useState("");
  const streamRef  = useRef<MediaStream | null>(null);
  const timerRef   = useRef<NodeJS.Timeout | null>(null);

  const start = async () => {
    try {
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx      = new AudioContext();
      const source   = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      setActive(true); setError("");
      timerRef.current = setInterval(() => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        const avg  = data.reduce((a, b) => a + b, 0) / data.length;
        setDb(Math.round(avg * 0.6 + 20));
      }, 500);
    } catch { setError("Mic access denied"); }
  };

  const stop = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    if (timerRef.current) clearInterval(timerRef.current);
    setActive(false);
    // Keep last db reading — don't reset to null
  };

  useEffect(() => () => stop(), []);
  return { db, active, error, start, stop };
}

// Light sensor hook
function useLightSensor() {
  const [level,     setLevel]     = useState<number>(50);
  const [fromSensor,setFromSensor]= useState(false);

  useEffect(() => {
    if ("AmbientLightSensor" in window) {
      try {
        const sensor = new (window as any).AmbientLightSensor();
        sensor.addEventListener("reading", () => {
          setLevel(Math.min(100, Math.round((sensor.illuminance / 1000) * 100)));
          setFromSensor(true);
        });
        sensor.start();
      } catch { setFromSensor(false); }
    }
  }, []);

  return { level, fromSensor, setLevel };
}

export default function Dashboard() {
  const mic   = useMicrophone();
  const light = useLightSensor();

  const [snapshot,     setSnapshot]     = useState<Record<string, RoomState>>({});
  const [selectedRoom, setSelectedRoom] = useState(() => load("selectedRoom", "bedroom"));
  const [history,      setHistory]      = useState<any[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [lastUpdated,  setLastUpdated]  = useState("");
  const [backendError, setBackendError] = useState("");
  const [activeTab, setActiveTab] = useState<"environment"|"devices"|"health"|"weather"|"emotion"|"chat">(() => load("activeTab", "environment") as any);
  
  // Live overrides from user's device
  const [acOn,          setAcOn]          = useState(false);
  const [fanOn,         setFanOn]         = useState(false);
  const [currentMusic,  setCurrentMusic]  = useState(() => load("currentMusic", ""));
  const [devicePower,   setDevicePower]   = useState<number | null>(null);
  const [weatherTemp,   setWeatherTemp]   = useState<number | null>(() => load("weatherTemp", null));
  const [weatherPlace,  setWeatherPlace]  = useState(() => load("weatherPlace", ""));
  const [weatherResult, setWeatherResult] = useState<any>(() => load("weatherResult", null));
  const [weatherLoading,setWeatherLoading]= useState(false);

  const [healthForm,    setHealthForm]    = useState(() => load("healthForm", {
    temperature_c: 26, noise_db: 40, light_level: 20,
    sleep_hour: 23, wake_hour: 7, health_conditions: [] as string[],
  }));
  const [healthResult,  setHealthResult]  = useState<any>(null);

  const [emotionText,   setEmotionText]   = useState("");
  const [emotionResult, setEmotionResult] = useState<any>(null);
  const [emotionLoading,setEmotionLoading]= useState(false);

  const [chatMessages,  setChatMessages]  = useState<{role:string,content:string}[]>(() => load("chatMessages", []));
  const [chatInput,     setChatInput]     = useState("");
  const [chatLanguage,  setChatLanguage]  = useState(() => load("chatLanguage", "Hindi"));
  const [chatLoading,   setChatLoading]   = useState(false);

  // Persist
  useEffect(() => save("selectedRoom",  selectedRoom),  [selectedRoom]);
  useEffect(() => save("activeTab",     activeTab),     [activeTab]);
  useEffect(() => save("healthForm",    healthForm),    [healthForm]);
  useEffect(() => save("weatherPlace",  weatherPlace),  [weatherPlace]);
  useEffect(() => save("chatMessages",  chatMessages),  [chatMessages]);
  useEffect(() => save("chatLanguage",  chatLanguage),  [chatLanguage]);
  useEffect(() => save("currentMusic",  currentMusic),  [currentMusic]);
  useEffect(() => save("weatherTemp",   weatherTemp),   [weatherTemp]);
  useEffect(() => { if (weatherResult) save("weatherResult", weatherResult); }, [weatherResult]);

  // When weather updates, extract temperature
  useEffect(() => {
    if (weatherResult?.indoor_estimate?.temperature_c) {
      setWeatherTemp(weatherResult.indoor_estimate.temperature_c);
    }
  }, [weatherResult]);

  // Sync health form noise from microphone
  useEffect(() => {
    if (mic.db !== null) {
      setHealthForm(prev => ({ ...prev, noise_db: mic.db! }));
    }
  }, [mic.db]);

  // Sync health form light from sensor
  useEffect(() => {
    setHealthForm(prev => ({ ...prev, light_level: light.level }));
  }, [light.level]);

  // Sync health form temperature from weather
  useEffect(() => {
    if (weatherTemp !== null) {
      setHealthForm(prev => ({ ...prev, temperature_c: weatherTemp }));
    }
  }, [weatherTemp]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setBackendError("");
    try {
      const res  = await fetch(`${API_BASE}/environment/snapshot`);
      if (!res.ok) throw new Error(`Backend ${res.status}`);
      setSnapshot(await res.json());
      setLastUpdated(new Date().toLocaleTimeString());
      try {
        const h = await fetch(`${API_BASE}/environment/history/${selectedRoom}?limit=15`);
        const d = await h.json();
        if (d.history) setHistory([...d.history].reverse());
      } catch {}
    } catch (e: any) {
      setBackendError(e.message);
    } finally { setLoading(false); }
  }, [selectedRoom]);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => { const t = setInterval(refresh, 30000); return () => clearInterval(t); }, [refresh]);

  const getWeather = async (name?: string) => {
    const q = name || weatherPlace;
    if (!q.trim()) return;
    setWeatherLoading(true);
    try {
      const res = await fetch(`${API_BASE}/weather/place?name=${encodeURIComponent(q)}`);
      const data= await res.json();
      setWeatherResult(data);
    } catch { setWeatherResult({ error: "Weather fetch failed" }); }
    finally { setWeatherLoading(false); }
  };

  const getGPSWeather = () => {
    if (!navigator.geolocation) { alert("GPS not available"); return; }
    setWeatherLoading(true);
    navigator.geolocation.getCurrentPosition(
      async pos => {
        try {
          const res = await fetch(`${API_BASE}/weather/gps?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`);
          const data= await res.json();
          setWeatherResult(data);
          if (data.location?.name) setWeatherPlace(data.location.name);
        } finally { setWeatherLoading(false); }
      },
      () => { alert("GPS access denied"); setWeatherLoading(false); },
      { timeout: 10000 }
    );
  };

  const analyzeEmotion = async () => {
    if (!emotionText.trim()) return;
    setEmotionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/emotion/analyze`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ text: emotionText, user_id: USER_ID }),
      });
      setEmotionResult(await res.json());
    } catch { setEmotionResult({ error: "Backend sleeping — wait 30-60s and retry" }); }
    finally { setEmotionLoading(false); }
  };

  const analyzeHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/sleep/predict`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify(healthForm),
      });
      setHealthResult(await res.json());
    } catch { setHealthResult({ error: "Backend error" }); }
  };

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userMsg = { role:"user", content: chatInput };
    const msgs    = [...chatMessages, userMsg];
    setChatMessages(msgs); setChatInput(""); setChatLoading(true);
    try {
      const room = snapshot[selectedRoom];
      const res  = await fetch(`${API_BASE}/chat/message`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          messages: msgs, language: chatLanguage,
          user_emotion: emotionResult?.detected_emotion,
          room_conditions: room ? {
            temperature: weatherTemp || room.temperature_c,
            noise: mic.db || room.noise_db,
            comfort: room.comfort_score,
          } : null,
          user_id: USER_ID,
        }),
      });
      const d = await res.json();
      setChatMessages([...msgs, { role:"assistant", content: d.reply }]);
    } catch {
      setChatMessages([...msgs, { role:"assistant", content:"Could not connect. Try again." }]);
    } finally { setChatLoading(false); }
  };

  // Build live environment display
  const baseRoom   = snapshot[selectedRoom];
  const liveRoom   = baseRoom ? {
    ...baseRoom,
    temperature_c:  weatherTemp ?? baseRoom.temperature_c,
    noise_db:       mic.db      ?? baseRoom.noise_db,
    light_level:    light.level,
    power_watts:    devicePower ?? baseRoom.power_watts,
    ac_on:          acOn,
    fan_on:         fanOn,
    music_playing:  !!currentMusic,
  } : null;

 const TABS = [
    { id:"environment", label:"🏠 Environment" },
    { id:"devices",     label:"⚡ Devices" },
    { id:"health",      label:"❤️ Health & Sleep" },
    { id:"weather",     label:"🌤 Weather" },
    { id:"emotion",     label:"😊 Emotion" },
    { id:"chat",        label:"💬 Talk to AI" },
  ];

  const MUSIC_OPTIONS = [
    "","lo-fi / calm","upbeat / energetic","classical","Bollywood",
    "devotional / bhajans","jazz","podcast","silence",
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4 max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold">SmartHome AI</h1>
          <p className="text-xs text-gray-400">Intelligent Well-being System</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{lastUpdated}</span>
          <button onClick={refresh}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-sm px-3 py-2 rounded-lg">
            <RefreshCw size={14} className={loading?"animate-spin":""}/>
          </button>
        </div>
      </div>

      {backendError && (
        <div className="bg-red-900/30 border border-red-700/40 rounded-xl p-3 mb-4 text-xs text-red-300">
          ⚠️ {backendError} — Render free tier sleeps after 15 min. Wait 30-60s and refresh.
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-5 flex-wrap">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id as any)}
            className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
              activeTab===t.id ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── ENVIRONMENT ─────────────────────────────────────────────── */}
      {activeTab === "environment" && (
        <div>
          <div className="flex gap-2 mb-4 flex-wrap">
            {Object.keys(ROOMS).map(r => {
              const s = snapshot[r];
              return (
                <button key={r} onClick={() => setSelectedRoom(r)}
                  className={`px-3 py-2 rounded-xl text-sm font-medium ${
                    selectedRoom===r ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400"
                  }`}>
                  {ROOMS[r]}
                  {s && <span className={`ml-2 text-xs font-bold ${comfortColor(s.comfort_score)}`}>{s.comfort_score}</span>}
                </button>
              );
            })}
          </div>

          {loading && !liveRoom && (
            <div className="text-center py-12 text-gray-500">
              <RefreshCw size={24} className="animate-spin mx-auto mb-2"/>
              Loading... {backendError && <span className="text-xs text-red-400 block mt-1">Wait 30-60s — backend starting up</span>}
            </div>
          )}

          {liveRoom && (
            <>
              {/* Comfort score */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 mb-4 flex justify-between items-center">
                <div>
                  <p className="text-xs text-gray-400 mb-1">Comfort Score</p>
                  <p className={`text-5xl font-bold ${comfortColor(liveRoom.comfort_score)}`}>
                    {liveRoom.comfort_score}<span className="text-xl text-gray-400">/100</span>
                  </p>
                  <p className={`text-sm mt-1 ${comfortColor(liveRoom.comfort_score)}`}>
                    {comfortLabel(liveRoom.comfort_score)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-400">{ROOMS[selectedRoom]}</p>
                  <div className="flex items-center gap-1 mt-1 justify-end">
                    <Wifi size={12} className="text-green-400"/>
                    <span className="text-xs text-green-400">Live</span>
                  </div>
                  <p className="text-xs text-gray-500">{new Date().toLocaleTimeString()}</p>
                </div>
              </div>

              {/* Comfort suggestions */}
              {liveRoom.comfort_score < 60 && liveRoom.comfort_suggestions && (
                <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-4 mb-4">
                  <p className="text-sm font-medium text-yellow-300 mb-2 flex items-center gap-2">
                    <AlertTriangle size={14}/> How to improve comfort score
                  </p>
                  {liveRoom.comfort_suggestions.map((s, i) => (
                    <div key={i} className="flex justify-between text-sm py-1">
                      <span className="text-gray-300">• {s.action}</span>
                      <span className="text-green-400">+{s.expected_score_gain} pts</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Outside noise */}
              {liveRoom.outside_noise_source && (
                <div className={`rounded-xl p-4 mb-4 border ${
                  (liveRoom.outside_noise_db||0)>70
                    ? "bg-red-900/20 border-red-700/40"
                    : "bg-gray-800/60 border-gray-700/40"
                }`}>
                  <p className="text-xs text-gray-400 mb-1">Outside Noise</p>
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium text-white capitalize">{liveRoom.outside_noise_source.replace(/_/g," ")}</p>
                      <p className="text-xs text-gray-400">{liveRoom.outside_noise_desc}</p>
                    </div>
                    <p className={`text-2xl font-bold ${(liveRoom.outside_noise_db||0)>75?"text-red-400":(liveRoom.outside_noise_db||0)>55?"text-yellow-400":"text-green-400"}`}>
                      {liveRoom.outside_noise_db?.toFixed(1)} dB
                    </p>
                  </div>
                  {liveRoom.outside_noise_impact && (
                    <p className="text-xs text-gray-400 mt-1">{liveRoom.outside_noise_impact}</p>
                  )}
                </div>
              )}

              {/* Stats — live sources */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                <StatCard icon={<Thermometer size={18}/>} label="Temperature"
                  value={liveRoom.temperature_c} unit="°C"
                  sub={weatherTemp ? "from weather" : "simulated"}/>

                <StatCard icon={<Volume2 size={18}/>} label="Indoor Noise"
                  value={mic.db ?? liveRoom.noise_db} unit="dB"
                  sub={mic.active ? "live microphone" : "simulated"}/>

                <StatCard icon={<Zap size={18}/>} label="Power Usage"
                  value={liveRoom.power_watts} unit="W"
                  sub={devicePower ? "from device tab" : "simulated"}/>

                <StatCard icon={<Sun size={18}/>} label="Light Level"
                  value={liveRoom.light_level} unit="%"
                  sub={light.fromSensor ? "live sensor" : "manual/simulated"}/>

                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-xs text-gray-400 mb-2">AC / Fan Control</p>
                  <div className="flex gap-2">
                    <button onClick={() => { setAcOn(!acOn); if (!acOn) setFanOn(false); }}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-medium ${acOn ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-300"}`}>
                      {acOn ? "AC On" : "AC Off"}
                    </button>
                    <button onClick={() => { setFanOn(!fanOn); if (!fanOn) setAcOn(false); }}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-medium ${fanOn ? "bg-cyan-600 text-white" : "bg-gray-700 text-gray-300"}`}>
                      {fanOn ? "Fan On" : "Fan Off"}
                    </button>
                  </div>
                </div>

                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-xs text-gray-400 mb-2">Music Playing</p>
                  <select value={currentMusic} onChange={e => setCurrentMusic(e.target.value)}
                    className="w-full bg-gray-700 text-white text-xs rounded px-2 py-1.5">
                    {MUSIC_OPTIONS.map(m => (
                      <option key={m} value={m}>{m || "Not playing"}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Auto-detect not possible in browser</p>
                </div>
              </div>

              {/* Microphone monitor */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Volume2 size={14} className="text-blue-400"/>
                    <span className="text-sm font-medium">Live Microphone</span>
                    {mic.active && <span className="text-xs text-green-400">● Recording</span>}
                  </div>
                  <button onClick={mic.active ? mic.stop : mic.start}
                    className={`px-3 py-1 rounded-lg text-xs font-medium ${mic.active ? "bg-red-600 text-white" : "bg-green-600 text-white"}`}>
                    {mic.active ? "Stop" : "Start Mic"}
                  </button>
                </div>
                {mic.error && <p className="text-xs text-red-400">{mic.error}</p>}
                {mic.active && mic.db !== null && (
                  <div className="flex items-center gap-3">
                    <p className={`text-2xl font-bold ${mic.db>65?"text-red-400":mic.db>45?"text-yellow-400":"text-green-400"}`}>
                      {mic.db} dB
                    </p>
                    <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all ${mic.db>65?"bg-red-500":mic.db>45?"bg-yellow-500":"bg-green-500"}`}
                        style={{width:`${Math.min(100,mic.db)}%`}}/>
                    </div>
                  </div>
                )}
                {!mic.active && <p className="text-xs text-gray-500">Start mic to use real noise readings</p>}
              </div>

              {/* Light level */}
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Sun size={14} className="text-yellow-400"/>
                  <span className="text-sm font-medium">Light Level</span>
                  {light.fromSensor && <span className="text-xs text-green-400">● Live sensor</span>}
                  {!light.fromSensor && <span className="text-xs text-gray-500">Manual (sensor N/A on Windows)</span>}
                </div>
                {!light.fromSensor && (
                  <div className="flex items-center gap-3">
                    <input type="range" min={0} max={100} value={light.level}
                      onChange={e => light.setLevel(Number(e.target.value))}
                      className="flex-1 accent-yellow-400"/>
                    <span className="text-lg font-bold text-yellow-400 w-12">{light.level}%</span>
                  </div>
                )}
                {light.fromSensor && (
                  <p className="text-2xl font-bold text-yellow-400">{light.level}%</p>
                )}
              </div>

              {/* History chart */}
              {history.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5">
                  <p className="text-sm font-medium text-gray-300 mb-4">Comfort History</p>
                  <ResponsiveContainer width="100%" height={160}>
                    <LineChart data={history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151"/>
                      <XAxis dataKey="timestamp" tick={{fontSize:9,fill:"#9CA3AF"}}
                        tickFormatter={v => new Date(v).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}/>
                      <YAxis domain={[0,100]} tick={{fontSize:9,fill:"#9CA3AF"}}/>
                      <Tooltip
                        contentStyle={{background:"#1F2937",border:"1px solid #374151",borderRadius:"8px",fontSize:"12px"}}
                        labelFormatter={l => new Date(l).toLocaleTimeString()}/>
                      <Line type="monotone" dataKey="comfort_score" stroke="#60A5FA" strokeWidth={2} dot={false}/>
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── DEVICES ─────────────────────────────────────────────────── */}
      {activeTab === "devices" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Smart Device Timer & Bill Calculator</h2>
          <p className="text-sm text-gray-400 mb-4">
            Add devices without knowing watts. Get instant bill and AI saving suggestions.
          </p>
          <SmartEnergyCalculator apiBase={API_BASE} onPowerUpdate={setDevicePower}/>
        </div>
      )}

      {/* ── HEALTH & SLEEP ───────────────────────────────────────────── */}
      {activeTab === "health" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Health & Sleep Analysis</h2>
          <div className="bg-blue-900/20 border border-blue-700/30 rounded-xl p-3 mb-4 text-xs text-blue-300">
            ℹ️ Temperature auto-filled from Weather tab · Noise auto-filled from microphone · Light from screen sensor
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">
                Room Temp (°C) {weatherTemp && <span className="text-green-400">← from weather</span>}
              </label>
              <input type="number" value={healthForm.temperature_c}
                onChange={e => setHealthForm({...healthForm,temperature_c:Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">
                Noise (dB) {mic.active && <span className="text-green-400">← live mic</span>}
              </label>
              <input type="number" value={healthForm.noise_db}
                onChange={e => setHealthForm({...healthForm,noise_db:Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">
                Light (%) {light.fromSensor && <span className="text-green-400">← live sensor</span>}
              </label>
              <input type="number" value={healthForm.light_level}
                onChange={e => setHealthForm({...healthForm,light_level:Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Sleep Hour</label>
              <input type="number" value={healthForm.sleep_hour} min={18} max={26}
                onChange={e => setHealthForm({...healthForm,sleep_hour:Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Wake Hour</label>
              <input type="number" value={healthForm.wake_hour} min={4} max={12}
                onChange={e => setHealthForm({...healthForm,wake_hour:Number(e.target.value)})}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 text-white text-sm"/>
            </div>
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
                      health_conditions: cs.includes(c)?cs.filter(x=>x!==c):[...cs,c]
                    });
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    healthForm.health_conditions.includes(c)
                      ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
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

              {healthResult.recommendations?.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-sm font-medium mb-2">Recommendations</p>
                  {healthResult.recommendations.map((r: any, i: number) => (
                    <div key={i} className="text-sm py-1 border-b border-gray-700/30 last:border-0">
                      <span className="text-yellow-400">{r.issue}: </span>
                      <span className="text-white">{r.action}</span>
                    </div>
                  ))}
                </div>
              )}

              {healthResult.health_tips?.length > 0 && (
                <div className="space-y-2">
                  {healthResult.health_tips.map((tip: any, i: number) => (
                    <div key={i} className="bg-blue-900/20 border border-blue-700/40 rounded-xl p-4">
                      <p className="text-sm font-medium text-white">{tip.condition}</p>
                      <p className="text-xs text-gray-400 mb-1">{tip.tip}</p>
                      <p className="text-xs text-blue-400">Suggested: {tip.suggested_temp}°C · {tip.suggested_noise}dB</p>
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

              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <p className="text-sm font-medium mb-2">Ideal Environment Tonight</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <p className="text-gray-400">Temp: <span className="text-white">{healthResult.ideal_environment?.temperature_c}°C</span></p>
                  <p className="text-gray-400">Light: <span className="text-white">{healthResult.ideal_environment?.light_level}%</span></p>
                  <p className="text-gray-400">Sleep: <span className="text-white">{healthResult.ideal_environment?.recommended_sleep_time}</span></p>
                  <p className="text-gray-400">Wake: <span className="text-white">{healthResult.ideal_environment?.recommended_wake_time}</span></p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── WEATHER ─────────────────────────────────────────────────── */}
      {activeTab === "weather" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Weather</h2>
          <p className="text-sm text-gray-400 mb-3">
            Search any place worldwide — cities, villages, colonies, cantonments, districts.
          </p>

          <div className="flex gap-2 mb-2">
            <input value={weatherPlace} onChange={e => setWeatherPlace(e.target.value)}
              onKeyDown={e => e.key==="Enter" && getWeather()}
              placeholder="Ambala Cantt, Koramangala Bangalore, Dharavi Mumbai..."
              className="flex-1 bg-gray-800 rounded-xl px-4 py-3 text-white text-sm border border-gray-700"/>
            <button onClick={() => getWeather()} disabled={weatherLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-3 rounded-xl text-sm font-medium">
              {weatherLoading ? "..." : "Search"}
            </button>
            <button onClick={getGPSWeather} disabled={weatherLoading}
              title="Auto-detect my location"
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-3 rounded-xl text-sm">
              📍
            </button>
          </div>

          <p className="text-xs text-gray-500 mb-4">
            Uses 3 geocoding sources for maximum coverage. Try: "Kasol", "Ambala Cantt", "Sector 17 Chandigarh"
          </p>

          
          {weatherResult && !weatherResult.error && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                <p className="font-medium text-white text-lg">
                  {weatherResult.location?.name || weatherResult.location?.city || "Unknown"}
                </p>
                {weatherResult.location?.full && weatherResult.location.full !== weatherResult.location?.name && (
                  <p className="text-xs text-gray-400">{weatherResult.location.full}</p>
                )}
                {weatherResult.location?.detected_by && (
                  <p className="text-xs text-green-400">📍 {weatherResult.location.detected_by}</p>
                )}
                <p className="text-sm text-gray-400 mt-1">{weatherResult.outdoor?.condition}</p>

                <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                  <p className="text-gray-400">Outdoor: <span className="text-white font-medium">{weatherResult.outdoor?.temperature_c}°C</span></p>
                  <p className="text-gray-400">Feels like: <span className="text-white">{weatherResult.outdoor?.feels_like_c}°C</span></p>
                  <p className="text-gray-400">Humidity: <span className="text-white">{weatherResult.outdoor?.humidity_percent}%</span></p>
                  <p className="text-gray-400">Wind: <span className="text-white">{weatherResult.outdoor?.wind_speed_kmh} km/h</span></p>
                  <p className="text-gray-400 col-span-2">
                    Indoor estimate: <span className="text-white font-medium">{weatherResult.indoor_estimate?.temperature_c}°C</span>
                    <span className="text-green-400 text-xs ml-2">← used in Environment & Health tabs</span>
                  </p>
                </div>

                {weatherResult.other_matches?.length > 0 && (
                  <div className="mt-3 p-2 bg-yellow-900/20 border border-yellow-700/30 rounded-lg">
                    <p className="text-xs text-yellow-400 mb-1">Did you mean?</p>
                    {weatherResult.other_matches.map((m: any, i: number) => (
                      <button key={i}
                        onClick={async () => {
                          setWeatherLoading(true);
                          const r = await fetch(`${API_BASE}/weather/by-coordinates?lat=${m.lat}&lon=${m.lon}&name=${encodeURIComponent(m.name||m.display||"")}`);
                          setWeatherResult(await r.json());
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
                (weatherResult.sleep_impact?.sleep_weather_score||0)>=75
                  ? "bg-green-900/20 border-green-700/40"
                  : "bg-yellow-900/20 border-yellow-700/40"
              }`}>
                <p className="text-sm font-medium">Sleep Score Tonight: {weatherResult.sleep_impact?.sleep_weather_score}/100</p>
                <p className="text-sm text-gray-300">{weatherResult.sleep_impact?.overall}</p>
                {weatherResult.sleep_impact?.impacts?.map((imp: string, i: number) => (
                  <p key={i} className="text-xs text-gray-400 mt-1">• {imp}</p>
                ))}
              </div>

              {weatherResult.recommendations?.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-sm font-medium mb-2">Smart Recommendations</p>
                  {weatherResult.recommendations.map((r: string, i: number) => (
                    <p key={i} className="text-xs text-gray-300 py-1">• {r}</p>
                  ))}
                </div>
              )}

              {weatherResult.forecast_3day?.length > 0 && (
                <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                  <p className="text-sm font-medium mb-3">3-Day Forecast</p>
                  <div className="grid grid-cols-3 gap-2">
                    {weatherResult.forecast_3day.map((d: any, i: number) => (
                      <div key={i} className="text-center p-2 bg-gray-700/40 rounded-lg">
                        <p className="text-xs text-gray-400">{new Date(d.date).toLocaleDateString("en-IN",{weekday:"short"})}</p>
                        <p className="text-lg font-bold text-white">{d.max_temp}°</p>
                        <p className="text-xs text-gray-400">{d.min_temp}°</p>
                        {d.rain_probability > 0 && <p className="text-xs text-blue-400">{d.rain_probability}% rain</p>}
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
              <p className="text-gray-400 text-xs mt-1">{weatherResult.tip}</p>
            </div>
          )}
        </div>
      )}

      {/* ── EMOTION ─────────────────────────────────────────────────── */}
      {activeTab === "emotion" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Emotion Detection</h2>
          <p className="text-sm text-gray-400 mb-4">
            Type how you feel in any Indian language. System detects emotion and suggests
            an environment adjustment. First request may take 30-60s if backend was sleeping.
          </p>
          <textarea value={emotionText} onChange={e => setEmotionText(e.target.value)}
            placeholder="How are you feeling? Hindi, English, Tamil, any Indian language..."
            className="w-full bg-gray-800 rounded-xl px-4 py-3 text-white text-sm h-24 resize-none mb-3 border border-gray-700"/>
          <button onClick={analyzeEmotion} disabled={emotionLoading}
            className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white py-3 rounded-xl font-medium mb-4">
            {emotionLoading ? "Analyzing... (30-60s first time)" : "Detect Emotion"}
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
      
      {/* ── CHAT ────────────────────────────────────────────────────── */}
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

          <div className="flex-1 overflow-y-auto space-y-3 mb-4 min-h-0">
            {chatMessages.length === 0 && (
              <div className="text-center py-8">
                <p className="text-4xl mb-3">💬</p>
                <p className="text-gray-400 text-sm">Talk in {chatLanguage} — all 22 Indian languages supported</p>
                <div className="flex flex-wrap gap-2 justify-center mt-4">
                  {["Mera room kaisa hai?","Sleep tips batao","Bijli bill kaise kam karo",
                    "Main bahut stressed hoon","AC chalani chahiye?"].map(s => (
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
                <div className={`max-w-xs md:max-w-sm rounded-2xl px-4 py-3 text-sm ${
                  msg.role==="user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-gray-800 text-gray-100 rounded-bl-sm"
                }`}>{msg.content}</div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1">
                  {[0,0.1,0.2].map((d,i) => (
                    <div key={i} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{animationDelay:`${d}s`}}/>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <input value={chatInput} onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key==="Enter" && sendChat()}
              placeholder={`Type in ${chatLanguage}...`}
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

// ── Smart Energy Calculator ────────────────────────────────────────────────
function SmartEnergyCalculator({ apiBase, onPowerUpdate }: {
  apiBase: string;
  onPowerUpdate?: (watts: number) => void;
}) {
  const [categories,      setCategories]      = useState<any>(null);
  const [selectedDevices, setSelectedDevices] = useState<any[]>([]);
  const [result,          setResult]          = useState<any>(null);
  const [loading,         setLoading]         = useState(false);
  const [rate,            setRate]            = useState(6.0);

  useEffect(() => {
    fetch(`${apiBase}/smart-devices/categories`)
      .then(r => r.json()).then(setCategories).catch(() => {});
  }, [apiBase]);

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
      const res = await fetch(`${apiBase}/smart-devices/calculate-bill`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          devices: selectedDevices.map(d => ({
            category: d.category, device_key: d.device_key,
            quantity: d.quantity, hours: d.hours,
            option: d.option, is_on: d.is_on,
          })),
          electricity_rate: rate,
        }),
      });
      const data = await res.json();
      setResult(data);
      // Update power usage in environment tab
      const totalWatts = data.breakdown?.reduce(
        (sum: number, d: any) => sum + (d.watts || 0), 0
      ) || 0;
      onPowerUpdate?.(Math.round(totalWatts / 24)); // average hourly
    } finally { setLoading(false); }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-gray-400">₹</span>
        <input type="number" value={rate} onChange={e => setRate(Number(e.target.value))}
          className="w-20 bg-gray-800 rounded px-2 py-1 text-sm text-white" step={0.5}/>
        <span className="text-sm text-gray-400">per unit</span>
      </div>

      {categories && (
        <div className="mb-4 space-y-2">
          <p className="text-sm text-gray-400">Add devices (no watts needed):</p>
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
                  <select value={d.option||""} onChange={e => {const u=[...selectedDevices];u[idx]={...d,option:e.target.value};setSelectedDevices(u);}}
                    className="bg-gray-700 text-white text-xs rounded px-2 py-1">
                    {Object.keys(d.options).map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                )}
                {d.ask === "wattage" && d.options && (
                  <select value={d.option||""} onChange={e => {const u=[...selectedDevices];u[idx]={...d,option:e.target.value};setSelectedDevices(u);}}
                    className="bg-gray-700 text-white text-xs rounded px-2 py-1">
                    {Object.keys(d.options).map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                )}
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-400">Qty:</span>
                  <input type="number" value={d.quantity} min={1} max={20}
                    onChange={e => {const u=[...selectedDevices];u[idx]={...d,quantity:Number(e.target.value)};setSelectedDevices(u);}}
                    className="w-12 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
                </div>
                <div className="flex items-center gap-1">
                  <Clock size={12} className="text-gray-400"/>
                  <input type="number" value={d.hours} min={0} max={24} step={0.5}
                    onChange={e => {const u=[...selectedDevices];u[idx]={...d,hours:Number(e.target.value)};setSelectedDevices(u);}}
                    className="w-16 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
                  <span className="text-xs text-gray-400">h</span>
                </div>
                <button onClick={() => setSelectedDevices(prev => prev.filter((_,i) => i!==idx))}
                  className="text-red-400 text-xs">✕</button>
              </div>
            </div>
          ))}

          <button onClick={calculate} disabled={loading}
            className="w-full mt-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-xl font-medium">
            {loading ? "Calculating..." : "Calculate Bill & AI Suggestions"}
          </button>
        </div>
      )}

      {result && !result.error && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">Current Monthly Bill</p>
              <p className="text-3xl font-bold text-red-400">₹{result.monthly_bill}</p>
              <p className="text-xs text-gray-400">₹{result.daily_cost}/day</p>
            </div>
            <div className="bg-green-900/20 border border-green-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">After AI Suggestions</p>
              <p className="text-3xl font-bold text-green-400">₹{result.optimized_bill}</p>
              <p className="text-xs text-green-300">Save ₹{result.monthly_saving}/month</p>
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
                  <p className="text-green-400 text-xs">₹{s.saving}/day → ₹{Math.round(s.saving*30)}/month</p>
                </div>
              ))}
            </div>
          )}

          <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
            <p className="text-sm font-medium mb-2">Breakdown (highest cost first)</p>
            {result.breakdown?.map((d: any, i: number) => (
              <div key={i} className="flex justify-between text-sm py-1 border-b border-gray-700/30 last:border-0">
                <span className="text-gray-300">{d.device}</span>
                <span><span className="text-white font-medium">₹{d.cost}</span><span className="text-gray-400">/day</span></span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
