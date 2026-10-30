async function request(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let message = "Something went wrong";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((d) => d.msg).join(", ");
      }
    } catch (_) {}
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

const api = {
  createLink(originalUrl, expiresAt) {
    const body = { original_url: originalUrl };
    if (expiresAt) body.expires_at = expiresAt;
    return request("/api/links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },
  listLinks() {
    return request("/api/links");
  },
  getStats(code) {
    return request(`/api/links/${encodeURIComponent(code)}/stats`);
  },
  deleteLink(code) {
    return request(`/api/links/${encodeURIComponent(code)}`, { method: "DELETE" });
  },
};

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
