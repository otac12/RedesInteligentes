const express = require('express');
const { WebSocketServer } = require('ws');
const Database = require('better-sqlite3');
const path = require('path');

const app = express();
app.use(express.json());

// --- SQLite ---
const db = new Database(path.join(__dirname, 'datos.db'));
db.pragma('journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS lecturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperatura REAL,
    humedad REAL,
    latitud REAL,
    longitud REAL,
    gas_lp REAL,
    timestamp DATETIME DEFAULT (datetime('now','localtime'))
  )
`);

const insertStmt = db.prepare(`
  INSERT INTO lecturas (temperatura, humedad, latitud, longitud, gas_lp)
  VALUES (@temperatura, @humedad, @latitud, @longitud, @gas_lp)
`);

const selectByDate = db.prepare(`
  SELECT * FROM lecturas
  WHERE date(timestamp) = ?
  ORDER BY timestamp ASC
`);

// --- HTTP ---
const server = app.listen(3000, () => {
    const nets = require('os').networkInterfaces();
    const ip = Object.values(nets).flat().find(n => n.family === 'IPv4' && !n.internal)?.address || 'localhost';
    console.log(`→ http://${ip}:3000`);
});
const wss = new WebSocketServer({ server });

// Recibe datos de sensores (REST API)
app.post('/datos', (req, res) => {
    const { temperatura, humedad, latitud, longitud, gas_lp } = req.body;

    const result = insertStmt.run({ temperatura, humedad, latitud, longitud, gas_lp });
    const row = db.prepare('SELECT * FROM lecturas WHERE id = ?').get(result.lastInsertRowid);

    // Reenviar por WebSocket al frontend
    const payload = JSON.stringify(row);
    wss.clients.forEach(c => {
        if (c.readyState === 1) c.send(payload);
    });

    res.json({ status: 'ok', id: result.lastInsertRowid });
});

// Consultar lecturas por día
app.get('/api/lecturas', (req, res) => {
    const fecha = req.query.fecha || new Date().toISOString().slice(0, 10);
    const rows = selectByDate.all(fecha);
    res.json(rows);
});

app.get('/ping', (req, res) => res.json({ status: 'pong' }));

app.get('/', (req, res) => res.sendFile(__dirname + '/index.html'));
