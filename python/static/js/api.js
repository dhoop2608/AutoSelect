async function api(url, opts={}) {
  try {
    const r = await fetch(url, opts);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  } catch(e) {
    console.error(e);
    document.getElementById('db-status').textContent = '● Error';
    document.getElementById('db-status').className = 'badge';
    return null;
  }
}
