const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchRooms(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/environment/rooms`);
  const data = await res.json();
  return data.rooms;
}

export async function fetchRoomLive(room: string) {
  const res = await fetch(`${API_BASE}/environment/room/${room}`);
  return res.json();
}

export async function fetchSnapshot() {
  const res = await fetch(`${API_BASE}/environment/snapshot`);
  return res.json();
}

export async function fetchRoomHistory(room: string, limit = 20) {
  const res = await fetch(`${API_BASE}/environment/history/${room}?limit=${limit}`);
  return res.json();
}