const form = document.getElementById('gen-form');
const clearBtn = document.getElementById('clear');
const resultSection = document.getElementById('result-section');
const codeEl = document.getElementById('code');
const copyBtn = document.getElementById('copy');
const downloadBtn = document.getElementById('download');
const generateBtn = document.getElementById('generate');

function setLoading(isLoading) {
  generateBtn.disabled = isLoading;
  generateBtn.textContent = isLoading ? 'Generating…' : 'Generate Terraform';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  setLoading(true);
  codeEl.textContent = '';
  resultSection.classList.add('hidden');

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data?.error || `Request failed with ${res.status}`);
    }

    const data = await res.json();
    const code = (data && data.code) || '';

    codeEl.textContent = code;
    resultSection.classList.remove('hidden');
  } catch (err) {
    alert(err.message || 'Failed to generate code');
  } finally {
    setLoading(false);
  }
});

clearBtn.addEventListener('click', () => {
  form.reset();
  resultSection.classList.add('hidden');
  codeEl.textContent = '';
});

copyBtn.addEventListener('click', async () => {
  const text = codeEl.textContent || '';
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    copyBtn.textContent = 'Copied!';
    setTimeout(() => (copyBtn.textContent = 'Copy'), 1500);
  } catch (_) {}
});

downloadBtn.addEventListener('click', () => {
  const text = codeEl.textContent || '';
  if (!text) return;
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'main.tf';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});