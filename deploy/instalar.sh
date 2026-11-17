#!/usr/bin/env bash
# Instala la suite en un VPS Ubuntu (Oracle Cloud Always Free, Hetzner, etc.) con HTTPS automático.
# Uso (en el VPS, como usuario con sudo):
#   curl -fsSL <este archivo> -o instalar.sh   (o copiarlo)  y después:
#   DOMINIO=suite.midominio.com REPO=https://github.com/mateobartolome1901/suite-agencia.git bash instalar.sh
# Antes: subir el archivo .env a /opt/suite/.env (con SECRET_KEY, ADMINS, tokens…). Ver DESPLIEGUE.md.
set -euo pipefail
: "${DOMINIO:?Falta DOMINIO (ej. suite-plastia.duckdns.org)}"
: "${REPO:?Falta REPO (URL del repositorio)}"
DIR=/opt/suite

sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip git debian-keyring debian-archive-keyring apt-transport-https curl
# Caddy: servidor web con certificado HTTPS automático y gratis (Let's Encrypt)
if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
  sudo apt-get update -y && sudo apt-get install -y caddy
fi

sudo mkdir -p "$DIR" && sudo chown "$USER" "$DIR"
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull --ff-only; else git clone "$REPO" "$DIR.tmp" && cp -a "$DIR.tmp/." "$DIR/" && rm -rf "$DIR.tmp"; fi
python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt"
"$DIR/venv/bin/python" "$DIR/suite/tools/temas.py"
test -f "$DIR/.env" || { echo "Falta $DIR/.env: copialo antes (ver DESPLIEGUE.md)"; exit 1; }

# Servicio: un solo proceso (servidor web + worker cada 15 min). La base es SQLite en /opt/suite/datos.
mkdir -p "$DIR/datos"
sed "s#__DIR__#$DIR#g; s#__USUARIO__#$USER#g" "$DIR/deploy/suite.service" | sudo tee /etc/systemd/system/suite.service >/dev/null
sed "s#__DOMINIO__#$DOMINIO#g" "$DIR/deploy/Caddyfile" | sudo tee /etc/caddy/Caddyfile >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now suite
sudo systemctl restart suite caddy
# Firewall de Ubuntu (en Oracle además hay que abrir 80 y 443 en la «Security List» de la red)
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT || true
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT || true
echo "Listo: https://$DOMINIO"
