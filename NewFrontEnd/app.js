const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const crypto = require('crypto');
const { createPool } = require('mysql2');

// Konfiguracja bazy danych
const pool = createPool({
    host: "20.215.200.144",
    user: "traffic_user",
    password: "adminTrafficMonitor1!",
    database: "trafficmonitor",
    connectionLimit: 10,
});

// Funkcja do haszowania haseł
function generateHash(password, salt) {
    return crypto
        .createHash('sha256')
        .update(salt + password)
        .digest('hex');
}

// Inicjalizacja aplikacji Express
const app = express();
const port = 3000;

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Strona logowania
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'loginScreen.html'));
});

// Logowanie użytkownika
app.post('/login', (req, res) => {
    const { idEmployee, password } = req.body;

    // Sprawdzenie użytkownika w bazie danych
    pool.query('SELECT * FROM admins WHERE id = ?', [idEmployee], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).send('Błąd serwera');
        }

        if (results.length === 0) {
            return res.status(401).send('Nieprawidłowe ID lub hasło');
        }

        const user = results[0];
        const storedPassword = user.password;
        const salt = user.salt;

        // Porównanie hasła
        const generatedHash = generateHash(password, salt);
        if (generatedHash === storedPassword) {
            res.redirect('/mainScreen');
        } else {
            res.status(401).send('Nieprawidłowe ID lub hasło');
        }
    });
});

// Strona główna
app.get('/mainScreen', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'mainScreen.html'));
});

// API: Pobierz listę miejsc
app.get('/api/places', (req, res) => {
    pool.query('SELECT id, name, city FROM nameOfPlace', (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        console.log('Wynik zapytania do nameOfPlace:', results);
        res.json(results);
    });
});

// API: Pobierz statystyki dla wybranego miejsca
app.get('/api/stats/:placeId', (req, res) => {
    const placeId = req.params.placeId;

    const statsQuery = `
        SELECT 
            (SELECT COUNT(*) FROM car WHERE id_video IN 
                (SELECT id FROM video WHERE id_nameOfPlace = ?)) AS totalCars,
            (SELECT AVG(speed) FROM speedOfCar WHERE id_video IN 
                (SELECT id FROM video WHERE id_nameOfPlace = ?)) AS averageSpeed,
            (SELECT COUNT(*) FROM car WHERE ifRed = TRUE AND id_video IN 
                (SELECT id FROM video WHERE id_nameOfPlace = ?)) AS carsOnRed
    `;

    pool.query(statsQuery, [placeId, placeId, placeId], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        const stats = results[0];
        res.json({
            totalCars: stats.totalCars,
            averageSpeed: stats.averageSpeed || 0,
            carsOnRed: stats.carsOnRed,
        });
    });
});

// Uruchomienie serwera
app.listen(port, () => {
    console.log(`Serwer działa na http://localhost:${port}`);
});