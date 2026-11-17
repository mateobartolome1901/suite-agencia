// Pantalla de ingreso: muestra Google y, solo en local, el login de desarrollo.
fetch('/api/login-opciones').then(function (r) { return r.json(); }).then(function (o) {
  document.getElementById('google').hidden = !o.google;
  document.getElementById('dev').hidden = !o.dev;
  document.getElementById('nada').hidden = o.google || o.dev;
});
if (/error=sin-acceso/.test(location.search)) document.getElementById('error').hidden = false;
