// Reads charts JSON from a data attribute and renders all charts.
(function () {
  const el = document.getElementById("charts-data");
  if (!el) return;
  const charts = JSON.parse(el.dataset.json || "{}");

  // Pie
  new Chart(document.getElementById("chartPie"), {
    type: "pie",
    data: charts.pie,
    options: { responsive: true, plugins: { legend: { position: "bottom" } } }
  });

  // Age line
  new Chart(document.getElementById("chartAge"), {
    type: "line",
    data: charts.age,
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { suggestedMin: 0, title: { display: true, text: "Rate (%)" } } }
    }
  });

  // BMI line
  new Chart(document.getElementById("chartBMI"), {
    type: "line",
    data: charts.bmi,
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { suggestedMin: 0, title: { display: true, text: "Rate (%)" } } }
    }
  });

  // Glucose bars
  new Chart(document.getElementById("chartGlu"), {
    type: "bar",
    data: charts.glucose,
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom" } },
      scales: { y: { beginAtZero: true, title: { display: true, text: "Count" } } }
    }
  });

  // Smoking bars
  new Chart(document.getElementById("chartSmoke"), {
    type: "bar",
    data: charts.smoking,
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { suggestedMin: 0, title: { display: true, text: "Rate (%)" } } }
    }
  });
})();
