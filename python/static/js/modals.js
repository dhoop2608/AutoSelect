async function openVehicleModal(vid) {
  const v = allVehicles.find(x => x.vehicle_id === vid);
  document.getElementById('mv-title').textContent = `${v.brand} ${v.model}`;
  document.getElementById('mv-sub').textContent   = `${v.year} · ${v.fuel_type}${v.body_style ? ' · ' + v.body_style : ''}`;
  document.getElementById('modal-tab-details').innerHTML = `
    <div class="info-row"><span class="key">Brand</span><span class="val">${v.brand}</span></div>
    <div class="info-row"><span class="key">Model</span><span class="val">${v.model}</span></div>
    <div class="info-row"><span class="key">Year</span><span class="val">${v.year}</span></div>
    <div class="info-row"><span class="key">MSRP</span><span class="val">$${Number(v.price).toLocaleString()}</span></div>
    <div class="info-row"><span class="key">Fuel Type</span><span class="val">${v.fuel_type}</span></div>
    ${v.engine_type ? `<div class="info-row"><span class="key">Engine</span><span class="val">${v.engine_type}</span></div>` : ''}
    ${v.body_style  ? `<div class="info-row"><span class="key">Body Style</span><span class="val">${v.body_style}</span></div>` : ''}
  `;
  document.getElementById('modal-tab-availability').innerHTML = '<div class="loading">Loading…</div>';
  document.getElementById('modal-tab-financing').innerHTML    = '<div class="loading">Loading…</div>';
  document.getElementById('vehicle-tabs').style.display = '';
  switchTab('details', document.querySelector('#vehicle-tabs .tab'));
  document.getElementById('modal-vehicle').classList.add('open');
  loadAvailability(vid);
  loadFinancing(vid);
}

async function loadAvailability(vid) {
  const rows = await api(`/api/vehicles/${vid}/dealerships`);
  if (!rows) return;
  const el = document.getElementById('modal-tab-availability');
  if (!rows.length) { el.innerHTML = '<div class="empty-state"><p>Not stocked at any dealership.</p></div>'; return; }
  el.innerHTML = `<table style="width:100%">
    <thead><tr><th>Dealership</th><th>Location</th><th>Stock</th><th>Price</th><th>Status</th></tr></thead>
    <tbody>${rows.map(r => `<tr>
      <td style="font-weight:500">${r.dealership_name}</td><td>${r.location}</td>
      <td>${r.stock_quantity}</td><td>$${Number(r.dealer_price).toLocaleString()}</td>
      <td><span class="chip chip-${r.availability_status === 'available' ? 'available' : 'out'}">${r.availability_status}</span></td>
    </tr>`).join('')}</tbody></table>`;
}

async function loadFinancing(vid) {
  const rows = await api(`/api/vehicles/${vid}/financing`);
  if (!rows) return;
  const el = document.getElementById('modal-tab-financing');
  if (!rows.length) { el.innerHTML = '<div class="empty-state"><p>No financing options found.</p></div>'; return; }
  el.innerHTML = `<table style="width:100%">
    <thead><tr><th>Dealership</th><th>Rate</th><th>Term</th><th>Min Down</th></tr></thead>
    <tbody>${rows.map(r => `<tr>
      <td style="font-weight:500">${r.dealership_name}</td><td>${r.interest_rate}%</td>
      <td>${r.loan_term_months} mo</td><td>$${Number(r.min_down_payment).toLocaleString()}</td>
    </tr>`).join('')}</tbody></table>`;
}

function switchTab(name, el) {
  document.querySelectorAll('#vehicle-tabs .tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  ['details','availability','financing'].forEach(n => {
    document.getElementById('modal-tab-' + n).style.display = n === name ? '' : 'none';
  });
}

async function openAddInventoryModal() {
  const [vehicles, dealers] = await Promise.all([api('/api/vehicles'), api('/api/dealerships')]);
  document.getElementById('inv-vid').innerHTML = vehicles.map(v => `<option value="${v.vehicle_id}">${v.brand} ${v.model} ${v.year}</option>`).join('');
  document.getElementById('inv-did').innerHTML = dealers.map(d => `<option value="${d.dealership_id}">${d.dealership_name}</option>`).join('');
  document.getElementById('modal-add-inv').classList.add('open');
}

async function submitAddInventory() {
  const body = {
    vehicle_id:    parseInt(document.getElementById('inv-vid').value),
    dealership_id: parseInt(document.getElementById('inv-did').value),
    stock_quantity:parseInt(document.getElementById('inv-qty').value),
    price:         parseFloat(document.getElementById('inv-price').value),
  };
  if (!body.stock_quantity || !body.price) return alert('Please fill all fields.');
  await api('/api/admin/inventory', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  closeModal('modal-add-inv');
  showToast('Inventory added');
  loadAdminInventory();
}

function openEditModal(vid, did, qty, price) {
  document.getElementById('edit-vid').value   = vid;
  document.getElementById('edit-did').value   = did;
  document.getElementById('edit-qty').value   = qty;
  document.getElementById('edit-price').value = price;
  document.getElementById('modal-edit-inv').classList.add('open');
}

async function submitEditInventory() {
  const body = {
    vehicle_id:    parseInt(document.getElementById('edit-vid').value),
    dealership_id: parseInt(document.getElementById('edit-did').value),
    stock_quantity:parseInt(document.getElementById('edit-qty').value),
    price:         parseFloat(document.getElementById('edit-price').value),
  };
  await api('/api/admin/inventory', { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  closeModal('modal-edit-inv');
  showToast('Inventory updated');
  loadAdminInventory();
}

async function discontinueInventory() {
  if (!confirm('Mark this listing as discontinued?')) return;
  const body = {
    vehicle_id:    parseInt(document.getElementById('edit-vid').value),
    dealership_id: parseInt(document.getElementById('edit-did').value),
  };
  await api('/api/admin/inventory', { method: 'DELETE', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  closeModal('modal-edit-inv');
  showToast('Listing discontinued');
  loadAdminInventory();
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}
