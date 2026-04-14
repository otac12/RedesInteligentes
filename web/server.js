const express = require('express');
const { WebSocketServer } = require('ws');

const app = express();
app.use(express.json());

const server = app.listen(3000, () => console.log('→ http://localhost:3000'));
const wss = new WebSocketServer({ server });

// Endpoint que recibe el JSON
app.post('/datos', (req, res) => {
    const data = req.body;
    console.log('Recibido:', data);
    wss.clients.forEach(c => c.send(JSON.stringify(data)));
    res.json({ status: 'ok' });
});

app.get('/', (req, res) => res.sendFile(__dirname + '/index.html'));