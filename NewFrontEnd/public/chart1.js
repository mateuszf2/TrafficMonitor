const ctx = document.getElementById('lineChart');

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
      datasets: [{
        label: 'Nr of cars',
        data: [101, 56, 236, 258, 214, 275, 168, 226, 70, 146, 151, 284, 143, 58, 130, 52, 166, 78, 226, 185, 130, 272, 249, 128],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true
    }
  });