const body = document.getElementById("links-body");
const table = document.getElementById("links-table");
const empty = document.getElementById("empty");
const errorBox = document.getElementById("error");

function isExpired(link) {
  if (!link.is_active) return true;
  return link.expires_at && new Date(link.expires_at) <= new Date();
}

function renderRow(link) {
  const tr = document.createElement("tr");
  const status = isExpired(link)
    ? '<span class="badge expired">Expired</span>'
    : '<span class="badge active">Active</span>';

  tr.innerHTML = `
    <td><a href="${escapeHtml(link.short_url)}" target="_blank" rel="noopener">${escapeHtml(link.short_code)}</a></td>
    <td class="url" title="${escapeHtml(link.original_url)}">${escapeHtml(link.original_url)}</td>
    <td>${link.click_count}</td>
    <td>${status}</td>
    <td class="actions">
      <a class="btn small" href="stats.html?code=${encodeURIComponent(link.short_code)}">Stats</a>
      <button class="small secondary" data-copy="${escapeHtml(link.short_url)}">Copy</button>
      <button class="small danger" data-delete="${escapeHtml(link.short_code)}">Delete</button>
    </td>`;
  return tr;
}

async function load() {
  errorBox.hidden = true;
  try {
    const links = await api.listLinks();
    body.innerHTML = "";
    table.hidden = links.length === 0;
    empty.hidden = links.length !== 0;
    links.forEach((link) => body.appendChild(renderRow(link)));
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  }
}

body.addEventListener("click", async (event) => {
  const copyUrl = event.target.dataset.copy;
  const deleteCode = event.target.dataset.delete;

  if (copyUrl) {
    await navigator.clipboard.writeText(copyUrl);
    event.target.textContent = "Copied!";
    setTimeout(() => (event.target.textContent = "Copy"), 1500);
  }

  if (deleteCode && confirm(`Delete ${deleteCode} and all its click data?`)) {
    try {
      await api.deleteLink(deleteCode);
      load();
    } catch (err) {
      errorBox.textContent = err.message;
      errorBox.hidden = false;
    }
  }
});

load();
