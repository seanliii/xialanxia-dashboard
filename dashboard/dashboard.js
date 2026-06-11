
// CLOCK
function updateClock() {
  const now = new Date();
  const opts = { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
  document.getElementById('clock').textContent = now.toLocaleTimeString('zh-CN', opts) + ' CST';
}
setInterval(updateClock, 1000);
updateClock();

// PAGE NAVIGATION — must be on window for inline onclick handlers
window.showPage = function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.sidebar-item').forEach(b => b.classList.remove('active'));

  const page = document.getElementById('page-' + name);
  if (page) page.classList.add('active');

  // match nav button
  document.querySelectorAll('.nav-btn').forEach(b => {
    if (b.getAttribute('onclick') && b.getAttribute('onclick').includes(name)) b.classList.add('active');
  });
  document.querySelectorAll('.sidebar-item').forEach(b => {
    if (b.getAttribute('onclick') && b.getAttribute('onclick').includes(name)) b.classList.add('active');
  });
}

// SKILL SEARCH
window.filterSkills = function filterSkills(query) {
  const cards = document.querySelectorAll('.skill-card');
  const q = query.toLowerCase();
  cards.forEach(c => {
    const text = c.textContent.toLowerCase();
    c.style.display = (!q || text.includes(q)) ? '' : 'none';
  });
}

// AUTO-REFRESH indicator
let lastRefresh = Date.now();
setInterval(() => {
  const age = Math.floor((Date.now() - lastRefresh) / 1000);
  // could update a "last updated" field here
}, 30000);
