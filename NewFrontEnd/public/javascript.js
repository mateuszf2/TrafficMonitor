async function showStats() {
    try {
        const selectElement = document.getElementById('intersection-select');
        const placeId = selectElement.value;

        if (!placeId) {
            alert('Wybierz skrzyżowanie, aby zobaczyć statystyki!');
            return;
        }

        const response = await fetch(`/api/stats/${placeId}`);
        const stats = await response.json();

        const statsDisplay = document.getElementById('stats-display');
        statsDisplay.innerHTML = `
            <p>Łączna liczba pojazdów: ${stats.totalCars}</p>
            <p>Średnia prędkość: ${stats.averageSpeed.toFixed(2)} km/h</p>
            <p>Pojazdy na czerwonym świetle: ${stats.carsOnRed}</p>
        `;
    } catch (error) {
        console.error('Błąd podczas ładowania statystyk:', error);
        alert('Nie udało się załadować statystyk.');
    }
}

// Ensure that one section is visible by default (e.g., "Analiza")
document.addEventListener('DOMContentLoaded', () => {
    showSection('analiza'); // Replace 'analiza' with the default section's ID if needed
});

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

// Wywołaj funkcję po załadowaniu strony
document.addEventListener('DOMContentLoaded', loadPlaces);

function showSection(sectionId) {
    // Ukryj wszystkie sekcje
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });

    // Pokaż wybraną sekcję
    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.style.display = 'block';
    }
}