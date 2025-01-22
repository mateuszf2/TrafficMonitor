const ctx = document.getElementById('lineChart')
const lineChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], 
        datasets: [{
            label: 'Nr of cars', 
            data: [], 
            borderColor: 'rgba(75, 192, 192, 1)', 
            borderWidth: 1,
            fill: false,
            tension: 0.1, 
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
                title: {
                    display: true,
                    text: 'Hour' 
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Nr of cars'
                }
            }
        }
    }
});