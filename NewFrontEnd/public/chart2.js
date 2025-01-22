const barCtx = document.getElementById('barChart');

const barChart = new Chart(barCtx, {
    type: 'bar',
    data: {
        labels: ['Red Light', 'Green Light'],
        datasets: [{
            data: [0, 0], 
            backgroundColor: ['rgba(255, 99, 132, 0.5)', 'rgba(75, 192, 192, 0.5)'],
            borderColor: ['rgba(255, 99, 132, 1)', 'rgba(75, 192, 192, 1)'],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: false 
            }
        },
        scales: {
            x: {
                display: true
            },
            y: {
                beginAtZero: true
            }
        }
    }
});