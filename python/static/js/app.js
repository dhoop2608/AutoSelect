document.addEventListener('DOMContentLoaded', async () => {
  document.querySelectorAll('.modal-overlay').forEach(o =>
    o.addEventListener('click', e => {
      if (e.target === o) o.classList.remove('open')
    })
  );

  await loadVehicles();
  await loadStats();
  await populateAdminDealerFilter();
});