function vehicleCard(v) {
  const inStock = v.total_stock > 0;
  return `<div class="vehicle-card" onclick="openVehicleModal(${v.vehicle_id})">
    <div class="vc-header">
      <div class="vc-brand">${v.brand}</div>
      <div class="vc-model">${v.model}</div>
      <div class="vc-year">${v.year}</div>
      <span class="vc-fuel-badge fuel-${v.fuel_type}">${v.fuel_type}</span>
    </div>
    <div class="vc-body">
      <div class="vc-price">$${Number(v.price).toLocaleString()} <span>MSRP</span></div>
      <div class="vc-meta">
        ${v.body_style  ? `<span class="vc-meta-item">${v.body_style}</span>`  : ''}
        ${v.engine_type ? `<span class="vc-meta-item">${v.engine_type}</span>` : ''}
      </div>
    </div>
    <div class="vc-footer">
      <span class="stock-indicator ${inStock ? 'in-stock' : 'no-stock'}">
        <span class="stock-dot"></span>
        ${inStock ? v.total_stock + ' in stock' : 'Out of stock'}
      </span>
      <span style="font-size:12px;color:var(--text-3)">${v.dealership_count || 0} dealer${v.dealership_count !== 1 ? 's' : ''}</span>
    </div>
  </div>`;
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = '✓ ' + msg;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2800);
}

document.querySelectorAll('.modal-overlay').forEach(o =>
  o.addEventListener('click', e => { if (e.target === o) o.classList.remove('open'); })
);
