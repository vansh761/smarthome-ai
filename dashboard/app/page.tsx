"use client";

import { useEffect, useState, useCallback, useRef } from "react";
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

function saveToStorage(key: string, value: any) {
  try {
    localStorage.setItem(`smarthome_${key}`, JSON.stringify(value));
  } catch {}
}

function loadFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(`smarthome_${key}`);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
}

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

function SmartEnergyCalculator({ apiBase }: { apiBase: string }) {
  const [categories, setCategories] = useState<any>(null);
  const [selectedDevices, setSelectedDevices] = useState<any[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [rate, setRate] = useState(6.0);

  useEffect(() => {
    fetch(`${apiBase}/smart-devices/categories`)
      .then(r => r.json())
      .then(setCategories);
  }, [apiBase]);

  const addDevice = (catKey: string, devKey: string, dev: any) => {
    setSelectedDevices(prev => [...prev, {
      category:   catKey,
      device_key: devKey,
      label:      dev.label,
      watts:      dev.watts,
      ask:        dev.ask,
      options:    dev.options,
      quantity:   1,
      hours:      8,
      option:     dev.options ? Object.keys(dev.options)[0] : null,
      is_on:      true,
    }]);
  };

  const removeDevice = (idx: number) => {
    setSelectedDevices(prev => prev.filter((_, i) => i !== idx));
  };

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/smart-devices/calculate-bill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          devices: selectedDevices.map(d => ({
            category:   d.category,
            device_key: d.device_key,
            quantity:   d.quantity,
            hours:      d.hours,
            option:     d.option,
            is_on:      d.is_on,
          })),
          electricity_rate: rate,
        }),
      });
      setResult(await res.json());
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-gray-400">Rate: ₹</span>
        <input type="number" value={rate} onChange={e => setRate(Number(e.target.value))}
          className="w-20 bg-gray-800 rounded px-2 py-1 text-sm text-white" step={0.5}/>
        <span className="text-sm text-gray-400">/unit</span>
      </div>

      {/* Category selector */}
      {categories && (
        <div className="mb-4">
          <p className="text-sm text-gray-400 mb-2">Add devices to your home:</p>
          <div className="space-y-2">
            {Object.entries(categories).map(([catKey, cat]: [string, any]) => (
              <details key={catKey} className="bg-gray-800/60 border border-gray-700/40 rounded-xl">
                <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-300">
                  {cat.label}
                </summary>
                <div className="px-4 pb-3 flex flex-wrap gap-2">
                  {Object.entries(cat.devices).map(([devKey, dev]: [string, any]) => (
                    <button key={devKey}
                      onClick={() => addDevice(catKey, devKey, dev)}
                      className="px-3 py-1.5 bg-gray-700 hover:bg-blue-700 text-xs rounded-lg text-gray-300 transition-colors">
                      + {dev.label}
                    </button>
                  ))}
                </div>
              </details>
            ))}
          </div>
        </div>
      )}

      {/* Selected devices */}
      {selectedDevices.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-400 mb-2">Your devices:</p>
          <div className="space-y-2">
            {selectedDevices.map((d, idx) => (
              <div key={idx} className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-white flex-1">{d.label}</span>
                  {d.ask === "tons" && d.options && (
                    <select value={d.option || ""}
                      onChange={e => {
                        const u = [...selectedDevices];
                        u[idx] = { ...d, option: e.target.value };
                        setSelectedDevices(u);
                      }}
                      className="bg-gray-700 text-white text-xs rounded px-2 py-1">
                      {Object.keys(d.options).map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  )}
                  {d.ask === "wattage" && d.options && (
                    <select value={d.option || ""}
                      onChange={e => {
                        const u = [...selectedDevices];
                        u[idx] = { ...d, option: e.target.value };
                        setSelectedDevices(u);
                      }}
                      className="bg-gray-700 text-white text-xs rounded px-2 py-1">
                      {Object.keys(d.options).map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  )}
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-400">Qty:</span>
                    <input type="number" value={d.quantity} min={1} max={20}
                      onChange={e => {
                        const u = [...selectedDevices];
                        u[idx] = { ...d, quantity: Number(e.target.value) };
                        setSelectedDevices(u);
                      }}
                      className="w-12 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-400">Hrs:</span>
                    <input type="number" value={d.hours} min={0} max={24} step={0.5}
                      onChange={e => {
                        const u = [...selectedDevices];
                        u[idx] = { ...d, hours: Number(e.target.value) };
                        setSelectedDevices(u);
                      }}
                      className="w-16 bg-gray-700 rounded px-2 py-1 text-xs text-white"/>
                  </div>
                  <button onClick={() => removeDevice(idx)}
                    className="text-red-400 hover:text-red-300 text-xs px-2">✕</button>
                </div>
              </div>
            ))}
          </div>

          <button onClick={calculate} disabled={loading}
            className="w-full mt-3 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium">
            {loading ? "Calculating..." : "Calculate My Bill"}
          </button>
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">Current Monthly Bill</p>
              <p className="text-3xl font-bold text-red-400">₹{result.monthly_bill}</p>
            </div>
            <div className="bg-green-900/20 border border-green-700/40 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-400">After AI Suggestions</p>
              <p className="text-3xl font-bold text-green-400">₹{result.optimized_bill}</p>
            </div>
          </div>

          {result.suggestions?.length > 0 && (
            <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-4">
              <p className="text-sm font-medium mb-2 text-yellow-300">AI Suggestions — Save ₹{result.monthly_saving}/month</p>
              {result.suggestions.map((s: any, i: number) => (
                <div key={i} className="text-sm mb-1">
                  <span className="text-white">{s.device}:</span>
                  <span className="text-gray-300"> {s.suggestion}</span>
                  <span className="text-green-400"> (save ₹{s.saving}/day)</span>
                </div>
              ))}
            </div>
          )}

          <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
            <p className="text-sm font-medium mb-2">Breakdown (highest cost first)</p>
            {result.breakdown?.map((d: any, i: number) => (
              <div key={i} className="flex justify-between text-sm py-1 border-b border-gray-700/30 last:border-0">
                <span className="text-gray-300">{d.device}</span>
                <span className="text-gray-400">{d.hours}h → <span className="text-white font-medium">₹{d.cost}/day</span></span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MicrophoneMonitor({ onNoiseUpdate }: { onNoiseUpdate?: (db: number) => void }) {
  const [isListening, setIsListening]   = useState(false);
  const [noiseLevel,  setNoiseLevel]    = useState<number | null>(null);
  const [noiseLabel,  setNoiseLabel]    = useState("");
  const [error,       setError]         = useState("");
  const analyserRef   = useRef<AnalyserNode | null>(null);
  const streamRef     = useRef<MediaStream | null>(null);
  const intervalRef   = useRef<NodeJS.Timeout | null>(null);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx      = new AudioContext();
      const source   = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      setIsListening(true);
      setError("");

      intervalRef.current = setInterval(() => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        const avg    = data.reduce((a, b) => a + b, 0) / data.length;
        const db     = Math.round(avg * 0.6 + 20);
        setNoiseLevel(db);
        onNoiseUpdate?.(db);

        if (db < 30)       setNoiseLabel("Quiet");
        else if (db < 50)  setNoiseLabel("Normal");
        else if (db < 65)  setNoiseLabel("Moderate");
        else if (db < 80)  setNoiseLabel("Loud");
        else               setNoiseLabel("Very Loud");
      }, 500);
    } catch (e) {
      setError("Microphone access denied. Please allow microphone in browser settings.");
    }
  };

  const stopListening = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIsListening(false);
    setNoiseLevel(null);
    setNoiseLabel("");
  };

  useEffect(() => () => stopListening(), []);

  return (
    <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Volume2 size={16} className="text-blue-400"/>
          <span className="text-sm font-medium text-gray-300">Live Microphone Monitor</span>
        </div>
        <button
          onClick={isListening ? stopListening : startListening}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            isListening
              ? "bg-red-600 hover:bg-red-700 text-white"
              : "bg-green-600 hover:bg-green-700 text-white"
          }`}>
          {isListening ? "Stop" : "Start Mic"}
        </button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {isListening && noiseLevel !== null && (
        <div className="flex items-center gap-4">
          <div>
            <p className={`text-3xl font-bold ${
              noiseLevel > 65 ? "text-red-400" :
              noiseLevel > 45 ? "text-yellow-400" : "text-green-400"
            }`}>{noiseLevel} dB</p>
            <p className="text-xs text-gray-400">{noiseLabel}</p>
          </div>
          <div className="flex-1">
            <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  noiseLevel > 65 ? "bg-red-500" :
                  noiseLevel > 45 ? "bg-yellow-500" : "bg-green-500"
                }`}
                style={{ width: `${Math.min(100, noiseLevel)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Live from laptop microphone</p>
          </div>
        </div>
      )}

      {!isListening && (
        <p className="text-xs text-gray-500">
          Click Start Mic to measure real noise level from your laptop microphone.
          Works on Chrome and Edge with HTTPS.
        </p>
      )}
    </div>
  );
}

function LightSensor() {
  const [lightLevel, setLightLevel] = useState<number | null>(null);
  const [supported,  setSupported]  = useState<boolean | null>(null);
  const [manual,     setManual]     = useState(50);

  useEffect(() => {
    if ("AmbientLightSensor" in window) {
      try {
        const sensor = new (window as any).AmbientLightSensor();
        sensor.addEventListener("reading", () => {
          const lux   = sensor.illuminance;
          const level = Math.min(100, Math.round((lux / 1000) * 100));
          setLightLevel(level);
        });
        sensor.addEventListener("error", () => setSupported(false));
        sensor.start();
        setSupported(true);
      } catch {
        setSupported(false);
      }
    } else {
      setSupported(false);
    }
  }, []);

  return (
    <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sun size={16} className="text-yellow-400"/>
        <span className="text-sm font-medium text-gray-300">
          Light Level
          {supported === true && <span className="ml-2 text-xs text-green-400">● Live from screen sensor</span>}
          {supported === false && <span className="ml-2 text-xs text-gray-500">● Manual (sensor not available on this device)</span>}
        </span>
      </div>

      {supported === true && lightLevel !== null ? (
        <div>
          <p className="text-3xl font-bold text-yellow-400">{lightLevel}%</p>
          <p className="text-xs text-gray-400 mt-1">Ambient light from laptop sensor</p>
        </div>
      ) : (
        <div>
          <div className="flex items-center gap-3">
            <input type="range" min={0} max={100} value={manual}
              onChange={e => setManual(Number(e.target.value))}
              className="flex-1 accent-yellow-400"/>
            <span className="text-lg font-bold text-yellow-400 min-w-12">{manual}%</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {supported === false
              ? "Ambient light sensor not available on this device/browser. Adjust manually."
              : "Loading sensor..."}
          </p>
        </div>
      )}
    </div>
  );
}

function MusicTagger({ onMusicUpdate }: { onMusicUpdate?: (music: string) => void }) {
  const [currentMusic, setCurrentMusic] = useState("");
  const [saved,        setSaved]        = useState(false);

  const MUSIC_PRESETS = [
    "lo-fi / calm instrumental",
    "upbeat / energetic",
    "classical",
    "Bollywood",
    "devotional / bhajans",
    "jazz",
    "hip-hop",
    "silence / no music",
    "podcast / talk",
    "news",
  ];

  const save = (music: string) => {
    setCurrentMusic(music);
    onMusicUpdate?.(music);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Music size={16} className="text-purple-400"/>
        <span className="text-sm font-medium text-gray-300">What are you playing?</span>
        {saved && <span className="text-xs text-green-400 ml-auto">Saved ✓</span>}
      </div>
      <p className="text-xs text-gray-500 mb-3">
        Browser privacy prevents detecting audio from YouTube or other apps.
        Tag it manually so the system can factor it into your emotion environment.
      </p>
      <div className="flex flex-wrap gap-2 mb-3">
        {MUSIC_PRESETS.map(m => (
          <button key={m}
            onClick={() => save(m)}
            className={`px-3 py-1.5 rounded-full text-xs transition-colors ${
              currentMusic === m
                ? "bg-purple-600 text-white"
                : "bg-gray-700 hover:bg-gray-600 text-gray-300"
            }`}>
            {m}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={currentMusic}
          onChange={e => setCurrentMusic(e.target.value)}
          placeholder="Or type custom: artist - song name"
          className="flex-1 bg-gray-700 rounded-lg px-3 py-2 text-sm text-white"
        />
        <button onClick={() => save(currentMusic)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-sm">
          Tag
        </button>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [snapshot,      setSnapshot]      = useState<Record<string, RoomState>>({});
  const [selectedRoom,  setSelectedRoom]  = useState<string>(
    () => loadFromStorage("selectedRoom", "bedroom")
  );
  const [history,       setHistory]       = useState<HistoryEntry[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [lastUpdated,   setLastUpdated]   = useState("");
  const [activeTab, setActiveTab] = useState<"environment"|"devices"|"health"|"emotion"|"sleep"|"energy"|"chat">("environment");
  const [chatMessages,  setChatMessages]  = useState<{role:string,content:string}[]>(
    () => loadFromStorage("chatMessages", [])
  );
  const [chatInput,     setChatInput]     = useState("");
  const [chatLanguage,  setChatLanguage]  = useState<string>(
    () => loadFromStorage("chatLanguage", "Hindi")
  );
  const [chatLoading,   setChatLoading]   = useState(false);

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
  const [healthForm,    setHealthForm]    = useState(
    () => loadFromStorage("healthForm", {
      temperature_c: 26, noise_db: 40, light_level: 20,
      sleep_hour: 23, wake_hour: 7, health_conditions: [] as string[],
    })
  );
  const [healthResult,  setHealthResult]  = useState<any>(null);

  // Emotion state
  const [emotionText,   setEmotionText]   = useState("");
  const [emotionResult, setEmotionResult] = useState<any>(null);
  const [emotionLoading,setEmotionLoading]= useState(false);

  // Weather state
  const [weatherPlace,  setWeatherPlace]  = useState<string>(
    () => loadFromStorage("weatherPlace", "Delhi")
  );
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

  useEffect(() => saveToStorage("chatMessages",  chatMessages),  [chatMessages]);
  useEffect(() => saveToStorage("chatLanguage",  chatLanguage),  [chatLanguage]);
  useEffect(() => saveToStorage("healthForm",    healthForm),    [healthForm]);
  useEffect(() => saveToStorage("weatherPlace",  weatherPlace),  [weatherPlace]);
  useEffect(() => saveToStorage("selectedRoom",  selectedRoom),  [selectedRoom]);
  
  const tabs = [
    { id: "environment", label: "🏠 Environment" },
    { id: "devices",     label: "⚡ Device Timer" },
    { id: "health",      label: "❤️ Health" },
    { id: "emotion",     label: "😊 Emotion" },
    { id: "sleep",       label: "🌙 Sleep & Weather" },
    { id: "energy",      label: "💡 Weather" },
    { id: "chat",        label: "💬 Talk to AI" },
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

              {/* Live microphone */}
              <div className="mb-4">
                <MicrophoneMonitor />
              </div>

              {/* Light sensor */}
              <div className="mb-4">
                <LightSensor />
              </div>

              {/* Music tagger */}
              <div className="mb-4">
                <MusicTagger />
              </div>

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
                      formatter={(v: any) => [`${v ?? 0}`, "Comfort"]}
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

      {/* ── CHAT TAB ─────────────────────────────────────────────────────── */}
      {activeTab === "chat" && (
        <div className="flex flex-col h-[70vh]">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-semibold">Talk to your Smart Home</h2>
            <select
              value={chatLanguage}
              onChange={e => setChatLanguage(e.target.value)}
              className="ml-auto bg-gray-800 text-white text-sm rounded-lg px-3 py-2 border border-gray-700">
              {["Hindi","Hinglish","English","Tamil","Telugu","Bengali",
                "Marathi","Gujarati","Kannada","Malayalam","Punjabi"].map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
            {chatMessages.length === 0 && (
              <div className="text-center py-12">
                <p className="text-4xl mb-3">💬</p>
                <p className="text-gray-400 text-sm">
                  Talk to your smart home in {chatLanguage}.
                </p>
                <p className="text-gray-500 text-xs mt-2">
                  Ask about your room, energy tips, sleep advice, or just chat.
                </p>
                <div className="flex flex-wrap gap-2 justify-center mt-4">
                  {[
                    "Mera room kaisa hai?",
                    "Sleep tips do",
                    "Bijli bill kaise kam karo",
                    "Main thak gaya hoon",
                    "Aaj ka mausam kaisa hai",
                  ].map(suggestion => (
                    <button key={suggestion}
                      onClick={() => setChatInput(suggestion)}
                      className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-full text-xs text-gray-300">
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatMessages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-xs md:max-w-md rounded-2xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-gray-800 text-gray-100 rounded-bl-sm"
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"/>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay:"0.1s"}}/>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay:"0.2s"}}/>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="flex gap-2">
            <input
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={async e => {
                if (e.key === "Enter" && chatInput.trim() && !chatLoading) {
                  const userMsg = { role: "user", content: chatInput };
                  const newMessages = [...chatMessages, userMsg];
                  setChatMessages(newMessages);
                  setChatInput("");
                  setChatLoading(true);
                  try {
                    const currentRoom = snapshot[selectedRoom];
                    const res  = await fetch(`${API_BASE}/chat/message`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        messages:        newMessages,
                        language:        chatLanguage,
                        user_emotion:    emotionResult?.detected_emotion,
                        room_conditions: currentRoom ? {
                          temperature: currentRoom.temperature_c,
                          noise:       currentRoom.noise_db,
                          comfort:     currentRoom.comfort_score,
                        } : null,
                        user_id: "dashboard_user",
                      }),
                    });
                    const data = await res.json();
                    setChatMessages([...newMessages, { role: "assistant", content: data.reply }]);
                  } finally {
                    setChatLoading(false);
                  }
                }
              }}
              placeholder={`Type in ${chatLanguage}... (Press Enter to send)`}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white text-sm"
            />
            <button
              onClick={async () => {
                if (!chatInput.trim() || chatLoading) return;
                const userMsg    = { role: "user", content: chatInput };
                const newMessages= [...chatMessages, userMsg];
                setChatMessages(newMessages);
                setChatInput("");
                setChatLoading(true);
                try {
                  const currentRoom = snapshot[selectedRoom];
                  const res  = await fetch(`${API_BASE}/chat/message`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      messages:        newMessages,
                      language:        chatLanguage,
                      user_emotion:    emotionResult?.detected_emotion,
                      room_conditions: currentRoom ? {
                        temperature: currentRoom.temperature_c,
                        noise:       currentRoom.noise_db,
                        comfort:     currentRoom.comfort_score,
                      } : null,
                      user_id: "dashboard_user",
                    }),
                  });
                  const data = await res.json();
                  setChatMessages([...newMessages, { role: "assistant", content: data.reply }]);
                } finally {
                  setChatLoading(false);
                }
              }}
              disabled={chatLoading || !chatInput.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-3 rounded-xl text-sm font-medium">
              Send
            </button>
          </div>
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
                      <h3 className="text-sm font-medium mb-2 text-blue-300">Health Tips & घरेलू उपाय</h3>
                      {healthResult.health_tips.map((tip: any, i: number) => (
                        <div key={i} className="mb-3 p-3 bg-gray-800/40 rounded-lg">
                          <p className="text-xs font-medium text-white mb-1">{tip.condition}</p>
                          <p className="text-xs text-gray-400 mb-2">{tip.tip}</p>
                          <p className="text-xs text-blue-400 mb-1">Suggested: {tip.suggested_temp}°C</p>
                          {tip.gharelu_upay?.length > 0 && (
                            <div className="mt-2 p-2 bg-green-900/20 rounded border border-green-700/30">
                              <p className="text-xs font-medium text-green-400 mb-1">🌿 घरेलू उपाय:</p>
                              {tip.gharelu_upay.map((upay: string, j: number) => (
                                <p key={j} className="text-xs text-gray-300">• {upay}</p>
                              ))}
                            </div>
                          )}
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
          <div className="flex gap-2 mb-2">
            <input
              value={weatherPlace}
              onChange={e => setWeatherPlace(e.target.value)}
              onKeyDown={e => e.key === "Enter" && getWeather()}
              placeholder="City, village, colony, district..."
              className="flex-1 bg-gray-800 rounded-xl px-4 py-3 text-white text-sm"
            />
            <button onClick={getWeather}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-xl text-sm font-medium">
              Search
            </button>
            <button
              onClick={() => {
                if (!navigator.geolocation) {
                  alert("GPS not available on this device/browser");
                  return;
                }
                navigator.geolocation.getCurrentPosition(
                  async (pos) => {
                    const res  = await fetch(
                      `${API_BASE}/weather/gps?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`
                    );
                    const data = await res.json();
                    setWeatherResult(data);
                  },
                  () => alert("GPS access denied. Please allow location access."),
                  { timeout: 10000 }
                );
              }}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-xl text-sm"
              title="Use my current location">
              📍 GPS
            </button>
          </div>
          <p className="text-xs text-gray-500 mb-4">
            Works for any city, village, colony, cantonment, district worldwide.
            Example: "Ambala Cantt", "Koramangala Bangalore", "Dharavi Mumbai"
          </p>

          {weatherResult && !weatherResult.error && (
            <div className="space-y-3">
              <div className="bg-gray-800/60 border border-gray-700/40 rounded-xl p-4">
                {weatherResult.other_matches && weatherResult.other_matches.length > 0 && (
                <div className="mt-2 p-2 bg-yellow-900/20 border border-yellow-700/30 rounded-lg">
                  <p className="text-xs text-yellow-400 mb-1">Other matching locations:</p>
                  {weatherResult.other_matches.map((m: any, i: number) => (
                    <button key={i}
                      onClick={async () => {
                        const res = await fetch(`${API_BASE}/weather/by-coordinates?lat=${m.lat}&lon=${m.lon}&name=${encodeURIComponent(m.name)}`);
                        setWeatherResult(await res.json());
                      }}
                      className="block text-xs text-blue-400 hover:text-blue-300 py-0.5">
                      → {m.name}
                    </button>
                  ))}
                </div>
              )}
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
      {/* ── ENERGY TAB ────────────────────────────────────────────────────── */}
      {activeTab === "energy" && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Smart Energy Calculator</h2>
          <p className="text-sm text-gray-400 mb-4">
            Select your devices — no need to know watts. System calculates bill automatically.
          </p>

          <SmartEnergyCalculator apiBase={API_BASE} />
        </div>
      )}

    </div>
  );
}
