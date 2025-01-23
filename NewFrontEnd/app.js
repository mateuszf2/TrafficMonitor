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

        const generatedHash = generateHash(password, salt);
        if (generatedHash === storedPassword) {
            res.redirect('/mainScreen');
        } else {
            res.status(401).send('Nieprawidłowe ID lub hasło');
        }
    });
});

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
    const { date } = req.query;

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

/*app.get('/api/hourlyStats/:placeId', (req, res) => {
    const placeId = req.params.placeId;
    const { date } = req.query;

    if (!date) {
        console.error('Nie podano daty.');
        return res.status(400).json({ error: 'Proszę podać datę w formacie YYYY-MM-DD' });
    }

    const hourlyStatsQuery = `
        SELECT 
            HOUR(v.timeSet) AS hour, 
            COUNT(c.id) AS carCount
        FROM car c
        INNER JOIN video v ON c.id_video = v.id
        WHERE v.id_nameOfPlace = ? AND DATE(v.timeSet) = ?
        GROUP BY HOUR(v.timeSet)
        ORDER BY hour ASC
    `;

    console.log(`Zapytanie SQL: ${hourlyStatsQuery}`);
    console.log(`Parametry: [${placeId}, ${date}]`);

    pool.query(hourlyStatsQuery, [placeId, date], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        if (!results || results.length === 0) {
            console.log('Brak wyników dla podanych parametrów.');
            return res.json([]); // Zwróć pustą listę
        }

        console.log('Wyniki zapytania:', results);
        res.json(results);
    });
});*/

app.get('/api/videos', (req, res) => {
    const { placeId, date } = req.query;
    //console.log(`placeId = ${placeId}, data = ${date}`);

    if (!placeId || !date){
        return res.status(400).json({ error: 'Proszę wybrać miejsce oraz datę' });
    }

    const statsVideoQuery = `
    SELECT v.id as id_video, v.link as nameOfVideo
    FROM video v
    WHERE v.id_nameOfPlace = ? AND
    DATE(v.timeSet) = ?
    `;

    pool.query(statsVideoQuery, [placeId, date], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        console.log('Wynik zapytania do video:', results);
        res.json(results);
    });

});

app.get('/api/cars', (req, res) => {
    const { id_video } = req.query;
    console.log(`video = ${id_video}`);

    if (!id_video){
        return res.status(400).json({ error: 'Proszę wybrać video' });
    }

    const statsCarQuery = `
    SELECT c.id as id_car
    FROM car c
    WHERE c.id_video = ?
    `;

    pool.query(statsCarQuery, [id_video], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        console.log('Wynik zapytania do video:', results);
        res.json(results);
    });

});

app.get('/api/carsStats', (req, res) => {
    const { id_video, id_car } = req.query;
    console.log(`video = ${id_video} car = ${id_car}`);

    if (!id_video || !id_car){
        return res.status(400).json({ error: 'Proszę wybrać video' });
    }

    const statsCarQuery = `
    SELECT 
    c.id AS id_car,
    c.ifRed AS ifRed,
    c.startTime AS startTime,
    COALESCE(AVG(doC.length), 0) AS avgDistance,
    COALESCE(AVG(soC.speed), 0) AS avgSpeed
    FROM car c
    LEFT JOIN speedOfCar soC 
    ON soC.id_car = c.id 
    AND soC.id_video = c.id_video
    LEFT JOIN distanceOfCar doC 
    ON doC.id_video1 = c.id_video  
    AND (
        (doC.id_car1 = c.id) OR (doC.id_car2 = c.id)
    )
    WHERE c.id_video = ? AND c.id = ?
    GROUP BY c.id;
    `;

    pool.query(statsCarQuery, [id_video, id_car], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        console.log('Wynik zapytania do video:', results[0]);
        res.json(results[0]);
    });

});

app.get('/api/periodStats/:placeId', (req, res) => {
    const placeId = req.params.placeId;
    const { period, date } = req.query;

    if (!date || !period) {
        return res.status(400).json({ error: 'Proszę podać datę i okres' });
    }

    let periodStatsQuery = '';
    let labels = [];

    if (period === 'day') {
        periodStatsQuery = `
            SELECT 
                HOUR(v.timeSet) AS hour, 
                COUNT(c.id) AS carCount
            FROM car c
            INNER JOIN video v ON c.id_video = v.id
            WHERE v.id_nameOfPlace = ? AND DATE(v.timeSet) = ?
            GROUP BY HOUR(v.timeSet)
            ORDER BY hour ASC;
        `;
        labels = Array.from({ length: 24 }, (_, i) => i); // Godziny od 0 do 23
    } else if (period === 'week') {
        periodStatsQuery = `
            SELECT DAYOFWEEK(v.timeSet) AS dayOfWeek, COUNT(c.id) AS carCount
            FROM car c
            LEFT JOIN video v ON c.id_video = v.id
            WHERE v.id_nameOfPlace = ? 
            AND YEAR(v.timeSet) = YEAR(?) 
            AND WEEK(v.timeSet, 1) = WEEK(?, 1)
            GROUP BY DAYOFWEEK(v.timeSet)
            ORDER BY dayOfWeek ASC;
        `;
        labels = Array.from({ length: 7 }, (_, i) => i + 1); // Dni tygodnia 1-7
    } else if (period === 'month') {
        periodStatsQuery = `
            SELECT DAY(v.timeSet) AS dayOfMonth, COUNT(c.id) AS carCount
            FROM car c
            INNER JOIN video v ON c.id_video = v.id
            WHERE v.id_nameOfPlace = ? AND MONTH(v.timeSet) = MONTH(?) AND YEAR(v.timeSet) = YEAR(?)
            GROUP BY DAY(v.timeSet)
            ORDER BY dayOfMonth ASC;
        `;
        labels = Array.from({ length: 31 }, (_, i) => i + 1); // Dni miesiąca 1-31
    } else if (period === 'year') {
        periodStatsQuery = `
            SELECT MONTH(v.timeSet) AS month, COUNT(c.id) AS carCount
            FROM car c
            LEFT JOIN video v ON c.id_video = v.id
            WHERE v.id_nameOfPlace = ? AND YEAR(v.timeSet) = ?
            GROUP BY MONTH(v.timeSet)
            ORDER BY month ASC;
        `;
        labels = Array.from({ length: 12 }, (_, i) => i + 1); // Miesiące 1-12
    }

    pool.query(periodStatsQuery, [placeId, date, date], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        const carCounts = labels.map(label => {
            const result = results.find(r => r.hour === label || r.dayOfWeek === label || r.dayOfMonth === label || r.month === label);
            return result ? result.carCount : 0; // Zwracamy 0 jeśli brak danych
        });

        res.json({
            labels,
            carCounts
        });
    });
});

app.get('/api/carSpeed', (req, res) => {
    const { id_video, id_car } = req.query;

    if (!id_video || !id_car) {
        return res.status(400).json({ error: 'Proszę podać id_video i id_car.' });
    }

    const query = `
        SELECT secondOfVideo as time, speed as speed
        FROM speedOfCar
        WHERE id_video = ? AND id_car = ?
        ORDER BY secondOfVideo ASC;
        `
    ;

    pool.query(query, [id_video, id_car], (err, results) => {
        if (err) {
            console.error('Błąd zapytania do bazy:', err);
            return res.status(500).json({ error: 'Błąd serwera' });
        }

        if (results.length === 0) {
            return res.json([]);
        }

        res.json(results);
    });
});

// Uruchomienie serwera
app.listen(port, () => {
    console.log(`Serwer działa na http://localhost:${port}`);
});