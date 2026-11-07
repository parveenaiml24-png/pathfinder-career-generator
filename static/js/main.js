document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => sidebar.classList.toggle("sidebar-open"));
  }

  document.querySelectorAll(".flash-close").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash").remove());
  });

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copy);
        const original = button.textContent;
        button.textContent = "Copied!";
        window.setTimeout(() => { button.textContent = original; }, 1400);
      } catch {
        button.textContent = "Select and copy";
      }
    });
  });

  if (window.skillChartData && window.Chart) {
    const data = window.skillChartData;
    const current = data.labels.map((label) => data.present.includes(label.toLowerCase()) ? 1 : 0);
    new Chart(document.getElementById("skillsChart"), {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          { label: "Current skills", data: current, backgroundColor: "#89b9a2", borderRadius: 6, barThickness: 13 },
          { label: "Skills to build", data: current.map((value) => value ? 0 : 1), backgroundColor: "#efd4c5", borderRadius: 6, barThickness: 13 }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => context.raw ? context.dataset.label : "" } } },
        scales: {
          x: { display: false, stacked: true, max: 1, grid: { display: false } },
          y: { stacked: true, grid: { display: false }, ticks: { color: "#656779", font: { family: "DM Sans", size: 12 } } }
        }
      }
    });
  }
});
