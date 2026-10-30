const errorBox = document.getElementById("error");
const content = document.getElementById("content");

async function load() {
  const code = new URLSearchParams(window.location.search).get("code");
  if (!code) {
    errorBox.textContent = "No link selected. Open stats from the My Links page.";
    errorBox.hidden = false;
    return;
  }

  try {
    const stats = await api.getStats(code);
    document.getElementById("original-url").textContent =
      `${stats.short_code} \u2192 ${stats.original_url}`;
    document.getElementById("total").textContent = stats.total_clicks;
    document.getElementById("last-click").textContent = stats.last_clicked_at
      ? new Date(stats.last_clicked_at).toLocaleString()
      : "-";
    content.hidden = false;

    if (stats.clicks_by_day.length === 0) {
      document.getElementById("chart").hidden = true;
      document.getElementById("no-data").hidden = false;
      return;
    }

    new Chart(document.getElementById("chart"), {
      type: "bar",
      data: {
        labels: stats.clicks_by_day.map((d) => d.day),
        datasets: [{ label: "Clicks per day (UTC)", data: stats.clicks_by_day.map((d) => d.clicks) }],
      },
      options: { scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    });
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  }
}

load();
