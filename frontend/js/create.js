const form = document.getElementById("create-form");
const errorBox = document.getElementById("error");
const resultBox = document.getElementById("result");
const shortUrlInput = document.getElementById("short-url");
const copyBtn = document.getElementById("copy-btn");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  resultBox.hidden = true;

  const url = document.getElementById("url").value.trim();
  const expiresLocal = document.getElementById("expires").value;
  // datetime-local gives local time; toISOString converts it to UTC for the API
  const expiresAt = expiresLocal ? new Date(expiresLocal).toISOString() : null;

  try {
    const link = await api.createLink(url, expiresAt);
    shortUrlInput.value = link.short_url;
    resultBox.hidden = false;
    form.reset();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shortUrlInput.value);
  } catch (_) {
    shortUrlInput.select();
    document.execCommand("copy");
  }
  copyBtn.textContent = "Copied!";
  setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
});
