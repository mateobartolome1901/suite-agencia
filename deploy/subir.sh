#!/usr/bin/env bash
# Sube la suite (última versión commiteada + .env) al servidor y la (re)instala. Se corre desde tu compu:
#   bash deploy/subir.sh
# Usa la llave ~/.ssh/suite_gcp (usuario «suite»). Ver DESPLIEGUE.md.
set -euo pipefail
SERVIDOR="${SERVIDOR:-suite@34.75.228.155}"
DOMINIO="${DOMINIO:-suite-agencia.duckdns.org}"
LLAVE="${LLAVE:-$HOME/.ssh/suite_gcp}"
SSH="ssh -i $LLAVE -o StrictHostKeyChecking=accept-new"
cd "$(dirname "$0")/.."
$SSH "$SERVIDOR" 'sudo mkdir -p /opt/suite && sudo chown $USER /opt/suite'
git archive --format=tar HEAD | $SSH "$SERVIDOR" 'tar -x -C /opt/suite'
scp -i "$LLAVE" -q .env "$SERVIDOR":/opt/suite/.env
$SSH "$SERVIDOR" "chmod 600 /opt/suite/.env && cd /opt/suite && DOMINIO=$DOMINIO bash deploy/instalar.sh"
