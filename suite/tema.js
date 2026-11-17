// Elige el tema del último negocio usado antes de pintar (evita un destello con los colores del otro negocio).
try { if (localStorage.getItem('suite_negocio') === 'tpa') document.getElementById('tema').href = 'temas/tpa.css'; } catch (e) { /* sin almacenamiento */ }
