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

        const response = await fetch(`/api/stats/${placeId}?date=${date}`);
        const stats = await response.json();

        if (response.status !== 200 || !stats) {
            throw new Error(stats.error || 'Nie udało się pobrać statystyk.');
        }

        const statsDisplay = document.getElementById('stats-display');
        statsDisplay.innerHTML = `
            <p>Łączna liczba pojazdów: ${stats.totalCars}</p>
            <p>Średnia prędkość: ${stats.averageSpeed.toFixed(2)} km/h</p>
            <p>Ilość aut, które przejechały na czerwonym: ${stats.carsOnRed}</p>
            <p>Średnia odległość między pojazdami: ${stats.averageDistance.toFixed(2)} m</p>
        `;

        updateBarChart(stats.carsOnRed, stats.totalCars - stats.carsOnRed);
        await showHourlyStats();
    } catch (error) {
        console.error('Błąd podczas ładowania statystyk:', error);
        alert('Nie udało się załadować statystyk.');
    }
}

function fillMissingHours(hourlyStats) {
    const filledStats = [];
    for (let hour = 0; hour < 24; hour++) {
        const stat = hourlyStats.find(s => s.hour === hour);
        filledStats.push({
            hour: hour,
            carCount: stat ? stat.carCount : 0,
        });
    }
    return filledStats;
}

async function showHourlyStats() {
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
}

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

async function showPeriodStats() {
    try {
        const selectElement = document.getElementById('intersection-select');
        const placeId = selectElement.value;
        const periodSelect = document.getElementById('period-select');
        const period = periodSelect.value;

        if (!placeId) {
            alert('Wybierz skrzyżowanie, aby zobaczyć statystyki!');
            return;
        }

        const dateInput = document.getElementById('date-input');
        const date = dateInput?.value;
        if (!date) {
            alert('Wybierz datę, aby zobaczyć dane!');
            return;
        }

        const response = await fetch(`/api/periodStats/${placeId}?date=${date}&period=${period}`);
        const periodStats = await response.json();

        if (response.status !== 200 || !periodStats) {
            throw new Error(periodStats.error || 'Nie udało się pobrać danych.');
        }

        const { labels, carCounts } = periodStats;

        updatePeriodChart(labels, carCounts);
    } catch (error) {
        console.error('Błąd podczas ładowania danych okresowych:', error);
        alert('Nie udało się załadować danych okresowych.');
    }
}

function updatePeriodChart(labels, carCounts) {
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
                        text: 'Okres'
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

// Ładowanie miejsc
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

// Pokaż sekcję
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

// Inicjalizacja po załadowaniu strony
document.addEventListener('DOMContentLoaded', () => {
    loadPlaces();
    showSection('analiza');
});