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
    } catch (error) {
        console.error('Błąd podczas ładowania statystyk:', error);
        alert('Nie udało się załadować statystyk.');
    }
}
function updateBarChart(carsOnRed, carsOnGreen) {
    if (barChart) {
        // Zaktualizuj dane istniejącego wykresu
        barChart.data.datasets[0].data = [carsOnRed, carsOnGreen];
        barChart.update();
    } else {
        // Utwórz nowy wykres, jeśli jeszcze nie istnieje
        const ctx = document.getElementById('barChart').getContext('2d');
        barChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Na czerwonym', 'Na zielonym'],
                datasets: [{
                    label: 'Liczba pojazdów',
                    data: [carsOnRed, carsOnGreen],
                    backgroundColor: ['#FF5733', '#33FF57'], // Kolory słupków
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

// Ładowanie miejsc
async function loadPlaces() {
    try {
        const response = await fetch('/api/places');
        const places = await response.json();

        const selectElement = document.getElementById('intersection-select');
        selectElement.innerHTML = ''; // Czyszczenie istniejących opcji

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
    showSection('analiza'); // Domyślnie wyświetl sekcję "analiza"
});