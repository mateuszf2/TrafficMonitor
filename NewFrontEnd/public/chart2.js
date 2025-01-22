const barCtx = document.getElementById('barChart');

const barChart = new Chart(barCtx, {
    type: 'bar',
    data: {
        labels: ['Red Light', 'Green Light'],
        datasets: [{
            label: 'Number of Cars',
            data: [0, 0], // Wartości początkowe
            backgroundColor: ['rgba(75, 192, 192, 0.5)', 'rgba(75, 192, 192, 0.5)'],
            borderColor: ['rgba(75, 192, 192, 1)', 'rgba(75, 192, 192, 1)'],
            borderWidth: 1
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