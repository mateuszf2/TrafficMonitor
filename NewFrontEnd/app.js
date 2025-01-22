const express = require('express'); //Tworzenie serwera
const bodyParser = require('body-parser'); //Middleware
const path = require('path'); //Obsługa scieżek (Node.js)
const crypto = require('crypto'); //Hashowanie
const { createPool } = require('mysql2'); //Bazy danych

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

// Pobierz listę miejsc
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

// Pobierz statystyki dla wybranego miejsca i dnia
app.get('/api/stats/:placeId', (req, res) => {
    const placeId = req.params.placeId;
    const { date } = req.query; // Pobierz datę z parametrów zapytania (np. ?date=YYYY-MM-DD)

    if (!date) {
        return res.status(400).json({ error: 'Proszę podać datę w formacie YYYY-MM-DD' });
    }

    const statsQuery = `
    SELECT 
        (SELECT COUNT(*) 
         FROM car 
         WHERE id_video IN 
             (SELECT id 
              FROM video 
              WHERE id_nameOfPlace = ? AND DATE(timeSet) = ?)) AS totalCars,
        (SELECT AVG(speed) 
         FROM speedOfCar 
         WHERE speed >= 2 AND id_video IN 
             (SELECT id 
              FROM video 
              WHERE id_nameOfPlace = ? AND DATE(timeSet) = ?)) AS averageSpeed,
        (SELECT COUNT(*) 
         FROM car 
         WHERE ifRed = TRUE 
           AND id_video IN 
             (SELECT id 
              FROM video 
              WHERE id_nameOfPlace = ? AND DATE(timeSet) = ?)) AS carsOnRed,
        (SELECT AVG(length) 
         FROM distanceOfCar 
         WHERE id_video1 IN 
             (SELECT id 
              FROM video 
              WHERE id_nameOfPlace = ? AND DATE(timeSet) = ?)) AS averageDistance
`;

    pool.query(statsQuery, [placeId, date, placeId, date, placeId, date, placeId, date], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        if (results.length > 0) {
            const stats = results[0];
            res.json({
                totalCars: stats.totalCars || 0,
                averageSpeed: stats.averageSpeed || 0,
                carsOnRed: stats.carsOnRed || 0,
                averageDistance: stats.averageDistance || 0,
            });
        } else {
            res.json({
                totalCars: 0,
                averageSpeed: 0,
                carsOnRed: 0,
                averageDistance: 0,
            });
        }
    });
});

// Uruchomienie serwera
app.listen(port, () => {
    console.log(`Serwer działa na http://localhost:${port}`);
});