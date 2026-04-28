// MLC - Script Global

// Smooth-scroll para anchors internos
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (href.length > 1) {
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  });
});

// Atajos de navegación
function goToDashboard() {
  window.location.href = 'dashboard.html';
}

function navigateToDashboard(type) {
  if (type === 'usuarios')   window.location.href = 'dashboard-usuarios.html';
  if (type === 'prestadores') window.location.href = 'dashboard-prestadores.html';
}

// Marcar menú activo según el archivo actual (en caso de que el HTML no lo declare)
document.addEventListener('DOMContentLoaded', function () {
  const currentFile = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav a').forEach(item => {
    if (item.getAttribute('href') === currentFile) {
      item.classList.add('active');
    }
  });
});
