function showPage(id, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + id).classList.add('active');
  if (el) el.classList.add('active');
  const [title, sub] = pageNames[id] || ['AutoSelect', ''];
  document.getElementById('topbar-title').textContent = title;
  document.getElementById('topbar-sub').textContent   = sub;
  document.getElementById('result-count').textContent = '';
  if (id === 'dealerships')     loadDealerships();
  if (id === 'admin-inventory') loadAdminInventory();
}

async function loadStats() {
  const s = await api('/api/stats/summary');
  if (!s) return;
  document.getElementById('s-vehicles').textContent = s.total_vehicles;
  document.getElementById('s-stock').textContent    = s.total_stock;
  document.getElementById('s-dealers').textContent  = s.total_dealerships;
  document.getElementById('s-ev').textContent       = s.electric_models;
  document.getElementById('s-avg').textContent      = '$' + Number(s.avg_price).toLocaleString();
}

async function loadVehicles() {
  const grid = document.getElementById('vehicle-grid');
  grid.innerHTML = '<div class="loading">Searching…</div>';
  const params = new URLSearchParams();
  const fuel   = document.getElementById('f-fuel').value;
  const body   = document.getElementById('f-body').value;
  const brand  = document.getElementById('f-brand').value.trim();
  const budget = document.getElementById('f-budget').value;
  if (fuel)   params.set('fuel',   fuel);
  if (body)   params.set('body',   body);
  if (brand)  params.set('brand',  brand);
  if (budget) params.set('budget', budget);
  const data = await api('/api/vehicles?' + params);
  if (!data) { grid.innerHTML = '<div class="empty-state"><p>Could not connect to database.</p></div>'; return; }
  allVehicles = data;
  document.getElementById('result-count').textContent = data.length + ' results';
  if (!data.length) {
    grid.innerHTML = '<div class="empty-state"><p>No vehicles found. Try adjusting your filters.</p></div>';
    return;
  }
  grid.innerHTML = data.map(v => vehicleCard(v)).join('');
}

function clearFilters() {
  document.getElementById('f-fuel').value   = '';
  document.getElementById('f-body').value   = '';
  document.getElementById('f-brand').value  = '';
  document.getElementById('f-budget').value = '';
  loadVehicles();
}

async function loadDealerships() {
  const list = document.getElementById('dealer-list');
  list.innerHTML = '<div class="loading">Loading…</div>';
  const data = await api('/api/dealerships');
  if (!data) return;
  allDealerships = data;
  list.innerHTML = data.map(d => `
    <div class="dealer-card" style="cursor:pointer" onclick="viewDealerInventory(${d.dealership_id}, '${d.dealership_name}')">
      <div class="dealer-icon">
        <svg width="18" height="18" fill="none" stroke="white" stroke-width="2" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      </div>
      <div>
        <div class="dealer-name">${d.dealership_name}</div>
        <div class="dealer-loc">📍 ${d.location || '—'}</div>
        <div class="dealer-phone">${d.phone_number || ''}</div>
      </div>
    </div>`).join('');
}

async function viewDealerInventory(did, name) {
  const rows = await api(`/api/dealerships/${did}/inventory`);
  if (!rows) return;
  document.getElementById('vehicle-tabs').style.display      = 'none';
  document.getElementById('modal-tab-details').style.display = '';
  document.getElementById('modal-tab-availability').style.display = 'none';
  document.getElementById('modal-tab-availability').innerHTML = '';
  document.getElementById('modal-tab-financing').style.display = 'none';
  document.getElementById('modal-tab-financing').innerHTML    = '';
  document.getElementById('mv-title').textContent = name;
  document.getElementById('mv-sub').textContent   = 'Inventory';
  document.getElementById('modal-tab-details').innerHTML = rows.length
    ? `<p style="font-size:13px;color:var(--text-2);margin-bottom:14px">${rows.length} vehicle model(s) listed</p>
       <table style="width:100%">
         <thead><tr><th>Vehicle</th><th>Year</th><th>Fuel</th><th>Stock</th><th>Price</th><th>Status</th></tr></thead>
         <tbody>${rows.map(r => `<tr>
           <td style="font-weight:500">${r.brand} ${r.model}</td><td>${r.year}</td><td>${r.fuel_type}</td>
           <td>${r.stock_quantity}</td><td>$${Number(r.price).toLocaleString()}</td>
           <td><span class="chip chip-${r.availability_status === 'available' ? 'available' : r.availability_status === 'out_of_stock' ? 'out' : 'discontinued'}">${r.availability_status}</span></td>
         </tr>`).join('')}</tbody>
       </table>`
    : '<div class="empty-state"><p>No inventory at this dealership.</p></div>';
  document.getElementById('modal-vehicle').classList.add('open');
}

async function loadAdminInventory() {
  const did = document.getElementById('admin-dealer-filter').value;
  let displayRows = [];
  if (did) {
    displayRows = await api(`/api/dealerships/${did}/inventory`) || [];
  } else {
    displayRows = await api('/api/vehicles') || [];
  }
  const tbody = document.getElementById('admin-inv-table');
  if (did) {
    tbody.innerHTML = displayRows.map(r => `<tr>
      <td>${r.vehicle_id}</td><td style="font-weight:500">${r.brand} ${r.model}</td>
      <td>${r.year}</td><td>${r.fuel_type}</td><td>${r.stock_quantity}</td>
      <td>$${Number(r.price).toLocaleString()}</td>
      <td><span class="chip chip-${r.availability_status === 'available' ? 'available' : r.availability_status === 'out_of_stock' ? 'out' : 'discontinued'}">${r.availability_status}</span></td>
      <td><button class="btn btn-secondary btn-sm" onclick="openEditModal(${r.vehicle_id},${did},${r.stock_quantity},${r.price})">Edit</button></td>
    </tr>`).join('');
  } else {
    tbody.innerHTML = displayRows.map(r => `<tr>
      <td>${r.vehicle_id}</td><td style="font-weight:500">${r.brand} ${r.model}</td>
      <td>${r.year}</td><td>${r.fuel_type}</td>
      <td>${r.total_stock || '—'}</td><td>$${Number(r.price).toLocaleString()}</td>
      <td><span class="chip chip-${r.total_stock > 0 ? 'available' : 'out'}">${r.total_stock > 0 ? 'available' : 'out of stock'}</span></td>
      <td><span style="font-size:11px;color:var(--text-3)">Select dealership</span></td>
    </tr>`).join('');
  }
}

async function submitNewVehicle() {
  const body = {
    brand:       document.getElementById('nv-brand').value.trim(),
    model:       document.getElementById('nv-model').value.trim(),
    year:        parseInt(document.getElementById('nv-year').value),
    price:       parseFloat(document.getElementById('nv-price').value),
    fuel_type:   document.getElementById('nv-fuel').value,
    body_style:  document.getElementById('nv-body').value || null,
    engine_type: document.getElementById('nv-engine').value.trim() || null,
  };
  if (!body.brand || !body.model || !body.year || !body.price) return alert('Please fill all required fields.');
  const res = await api('/api/admin/vehicles', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  if (res?.success) { showToast(`Vehicle added (ID: ${res.vehicle_id})`); clearNewVehicleForm(); }
}

function clearNewVehicleForm() {
  ['nv-brand','nv-model','nv-year','nv-price','nv-engine'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('nv-fuel').value = 'Gas';
  document.getElementById('nv-body').value = '';
}

async function populateAdminDealerFilter() {
  const dealers = await api('/api/dealerships');
  if (!dealers) return;
  allDealerships = dealers;
  const sel = document.getElementById('admin-dealer-filter');
  dealers.forEach(d => sel.add(new Option(d.dealership_name, d.dealership_id)));
}
