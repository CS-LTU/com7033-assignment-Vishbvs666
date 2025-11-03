// Keep JS minimal; no frameworks; CSP friendly

// Auto-dismiss flash messages 
window.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll(".flash");
  if (!flashes.length) return;
  setTimeout(() => flashes.forEach(f => f.remove()), 3500);
});
