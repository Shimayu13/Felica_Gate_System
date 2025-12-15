-- Initial schema for Felica Gate System
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  balance NUMERIC DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  idm TEXT UNIQUE,
  qr_token TEXT UNIQUE,
  label TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS stations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  name TEXT
);

CREATE TABLE IF NOT EXISTS gates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  station_id INTEGER,
  name TEXT,
  FOREIGN KEY(station_id) REFERENCES stations(id)
);

CREATE TABLE IF NOT EXISTS trips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  card_id INTEGER NOT NULL,
  station_in TEXT,
  gate_in TEXT,
  station_out TEXT,
  gate_out TEXT,
  status TEXT DEFAULT 'in_progress',
  entered_at DATETIME,
  exited_at DATETIME,
  device_id TEXT,
  timestamp DATETIME,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(card_id) REFERENCES cards(id)
);
