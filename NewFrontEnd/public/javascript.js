// Wyświetlanie statystyk
async function showStats() {
    try {
        const selectElement = document.getElementById('intersection-select');
        const placeId = selectElement.value;

        if (!placeId) {
            alert('Wybierz skrzyżowanie, aby zobaczyć statystyki!');
            return;
        }

        const dateInput = document.getElementById('date-input');
        const date = dateInput?.value;
        if (!date) {
            alert('Wybierz datę, aby zobaczyć statystyki!');
            return;
        }

        // Pobierz podstawowe statystyki
        const response = await fetch(`/api/stats/${placeId}?date=${date}`);
        const stats = await response.json();

        document.getElementById("car-select").innerHTML='';

        loadVideos(placeId, date);

        

        if (response.status !== 200 || !stats) {
            throw new Error(stats.error || 'Nie udało się pobrać statystyk.');
        }

        // Wyświetlanie podsumowujących statystyk
        const statsDisplay = document.getElementById('stats-display');
        statsDisplay.innerHTML = `
            <p>Łączna liczba pojazdów: ${stats.totalCars}</p>
            <p>Średnia prędkość: ${stats.averageSpeed.toFixed(2)} km/h</p>
            <p>Ilość aut, które przejechały na czerwonym: ${stats.carsOnRed}</p>
            <p>Średnia odległość między pojazdami: ${stats.averageDistance.toFixed(2)} m</p>
        `;

        // Zaktualizuj wykres słupkowy
        updateBarChart(stats.carsOnRed, stats.totalCars - stats.carsOnRed);

        // Automatyczne wywołanie showPeriodStats() z domyślnym okresem
        await showPeriodStats(placeId, date);
    } catch (error) {
        console.error('Błąd podczas ładowania statystyk:', error);
        alert('Nie udało się załadować statystyk.');
    }
}

/*function fillMissingHours(hourlyStats) {
    const filledStats = [];
    for (let hour = 0; hour < 24; hour++) {
        const stat = hourlyStats.find(s => s.hour === hour);
        filledStats.push({
            hour: hour,
            carCount: stat ? stat.carCount : 0,
        });
    }
    return filledStats;
}*/

/*async function showHourlyStats() {
    try {
        const selectElement = document.getElementById('intersection-select');
        const placeId = selectElement.value;

        if (!placeId) {
            alert('Wybierz skrzyżowanie, aby zobaczyć dane godzinowe!');
            return;
        }

        const dateInput = document.getElementById('date-input');
        const date = dateInput?.value;
        if (!date) {
            alert('Wybierz datę, aby zobaczyć dane godzinowe!');
            return;
        }

        console.log(`Pobieranie danych godzinowych dla miejsca ${placeId} na dzień ${date}`);

        const response = await fetch(`/api/hourlyStats/${placeId}?date=${date}`);
        const hourlyStats = await response.json();

        if (response.status !== 200 || !hourlyStats) {
            throw new Error(hourlyStats.error || 'Nie udało się pobrać danych godzinowych.');
        }

        const filledStats = fillMissingHours(hourlyStats);

        const hours = filledStats.map(stat => stat.hour);
        const carsPerHour = filledStats.map(stat => stat.carCount);

        updateLineChart(hours, carsPerHour);
    } catch (error) {
        console.error('Błąd podczas ładowania danych godzinowych:', error);
        alert('Nie udało się załadować danych godzinowych.');
    }
}*/

function updateBarChart(carsOnRed, carsOnGreen) {
    if (barChart) {
        barChart.data.datasets[0].data = [carsOnRed, carsOnGreen];
        barChart.update();
    } else {
        const ctx = document.getElementById('barChart').getContext('2d');
        barChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Na czerwonym', 'Na zielonym'],
                datasets: [{
                    label: 'Liczba pojazdów',
                    data: [carsOnRed, carsOnGreen],
                    backgroundColor: ['#FF5733', '#33FF57'],
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

function updateLineChart(hours, carsPerHour) {
    if (lineChart) {
        lineChart.data.datasets[0].data = carsPerHour;
        lineChart.data.labels = hours;
        lineChart.update();
    } else {
        const ctx = document.getElementById('lineChart').getContext('2d');
        lineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Liczba aut',
                    data: carsPerHour,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                    fill: false,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Godzina'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Ilość aut'
                        }
                    }
                }
            }
        });
    }
}

// Funkcja do wyświetlania statystyk okresowych
async function showPeriodStats(placeId, date) {
    try {
        const periodSelect = document.getElementById('period-select');
        const period = periodSelect.value;

        const response = await fetch(`/api/periodStats/${placeId}?date=${date}&period=${period}`);
        const periodStats = await response.json();

        if (response.status !== 200 || !periodStats) {
            throw new Error(periodStats.error || 'Nie udało się pobrać danych okresowych.');
        }

        const { labels, carCounts } = periodStats;

        // Zaktualizuj wykres okresowy
        updatePeriodChart(labels, carCounts);
    } catch (error) {
        console.error('Błąd podczas ładowania danych okresowych:', error);
        alert('Nie udało się załadować danych okresowych.');
    }
}

// Funkcja dynamicznie reagująca na zmianę okresu
function onPeriodChange() {
    const selectElement = document.getElementById('intersection-select');
    const dateInput = document.getElementById('date-input');

    const placeId = selectElement.value;
    const date = dateInput?.value;

    if (placeId && date) {
        showPeriodStats(placeId, date);
    }
}

function updatePeriodChart(labels, carCounts, xAxisLabel) {
    const ctx = document.getElementById('periodChart').getContext('2d');

    if (window.periodChart && window.periodChart.destroy) {
        window.periodChart.destroy();
    }

    window.periodChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Liczba aut',
                data: carCounts,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: xAxisLabel
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Liczba aut'
                    }
                }
            }
        }
    });
}

async function loadPlaces() {
    try {
        const response = await fetch('/api/places');
        const places = await response.json();

        const selectElement = document.getElementById('intersection-select');
        selectElement.innerHTML = '';

        places.forEach(place => {
            const option = document.createElement('option');
            option.value = place.id;
            option.textContent = `${place.name} (${place.city})`;
            selectElement.appendChild(option);
        });
    } catch (error) {
        console.error('Błąd podczas ładowania miejsc:', error);
    }
}

async function loadVideos(placeId, date) {
    try {
        const response = await fetch(`/api/videos?placeId=${placeId}&date=${date}`);
        const videos = await response.json();

        const selectElement = document.getElementById('video-select');
        selectElement.innerHTML = '';

        videos.forEach(video => {
            const option = document.createElement('option');
            option.value = video.id_video;
            option.textContent = `${video.nameOfVideo}`;
            selectElement.appendChild(option);
        });

        if (videos.length > 0) {
            loadCars(videos[0].id_video);
        }

        selectElement.addEventListener('change',() => {
            const selectedVideoId = selectElement.value;
            if (selectedVideoId){
                console.log(selectedVideoId);
                loadCars(selectedVideoId);
            }
        });
    } catch (error) {
        console.error('Błąd podczas ładowania miejsc:', error);
    }
}

async function loadCars(id_video) {
    try {
        const response = await fetch(`/api/cars?id_video=${id_video}`);
        const cars = await response.json();

        const selectElement = document.getElementById('car-select');
        selectElement.innerHTML = '';

        cars.forEach(car => {
            const option = document.createElement('option');
            option.value = car.id_car;
            option.textContent = `${car.id_car}`;
            selectElement.appendChild(option);
        });

        // Jeśli są jakieś auta, wybierz pierwsze i załaduj jego statystyki
        if (cars.length > 0) {
            selectElement.value = cars[0].id_car; // Wybierz pierwsze auto
            showCarsStats(); // Wywołaj funkcję do pobrania statystyk dla pierwszego auta
        }

        // Dodaj event listener na zmianę wyboru auta
        selectElement.addEventListener('change', showCarsStats);

    } catch (error) {
        console.error('Błąd podczas ładowania aut:', error);
    }
}

// Wyświetlanie statystyk
async function showCarsStats() {
    try {
        const selectElement = document.getElementById('video-select');
        const videoId = selectElement.value;

        if (!videoId) {
            alert('Wybierz filmik, aby zobaczyć statystyki!');
            return;
        }

        const carElement = document.getElementById('car-select');
        const car = carElement.value;

        if (!car) {
            alert('Wybierz datę, aby zobaczyć statystyki!');
            return;
        }

        console.log(videoId + " " + car)

        const response = await fetch(`/api/carsStats?id_video=${videoId}&id_car=${car}`);
        const stats = await response.json();

        if (response.status !== 200 || !stats) {
            throw new Error(stats.error || 'Nie udało się pobrać statystyk.');
        }
        
        const ifRedText = stats.ifRed? "TAK" : "NIE";

        // Wyświetlanie podsumowujących statystyk
        const statsDisplay = document.getElementById('speedOfCarStats-display');
        statsDisplay.innerHTML = `
            <p>Id auta: ${stats.id_car}</p>
            <p>Czy przejechał na czerwonym: ${ifRedText}</p>
            <p>Start auta: ${stats.startTime}</p>
            <p>Średnia prędkość auta: ${stats.avgSpeed ? stats.avgSpeed.toFixed(2) : stats.avgSpeed} km/h</p>
            <p>Średnia odległość między pojazdami: ${stats.avgDistance ? stats.avgDistance.toFixed(2) : stats.avgDistance} m</p>
        `;
        drawSpeedChart(videoId, car);
    } catch (error) {
        console.error('Błąd podczas ładowania statystyk:', error);
        //alert('Nie udało się załadować statystyk.');
    }
}

function showSection(sectionId) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });

    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.style.display = 'block';
    }
}

async function drawSpeedChart(id_video, id_car) {
    const response = await fetch(`/api/carSpeed?id_video=${id_video}&id_car=${id_car}`);
    const data = await response.json();

    if (!data || data.length === 0) {
        console.error('Brak danych dla tego auta i filmu');
        return;
    }

    const time = data.map(item => item.time); // Tablica czasów
    const speed = data.map(item => item.speed); // Tablica prędkości

    const ctx = document.getElementById('speedOfCarChart').getContext('2d');

    // Jeśli wykres już istnieje, zniszcz go
    if (window.speedChart) {
        window.speedChart.destroy();
    }


    window.speedChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: time, 
            datasets: [{
                label: 'Prędkość (km/h)',
                data: speed, 
                borderColor: 'rgba(75, 192, 192, 1)',
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Czas (s)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Prędkość (km/h)' 
                    }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadPlaces();
    showSection('analiza');
});