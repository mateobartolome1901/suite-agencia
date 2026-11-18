# Publicar la suite gratis

## Qué conviene

| Opción | Costo | Qué pasa |
|---|---|---|
| **VPS gratis de Oracle Cloud (Always Free)** — recomendado | US$0 para siempre | Un servidor propio (hasta 4 núcleos y 24 GB): corre la suite y el worker juntos, siempre prendido. Pide tarjeta solo para verificar identidad; no cobra si usás lo «Always Free». |
| VPS barato (Hetzner, Contabo) | ~US$4–6 por mes | Igual que el de Oracle, sin trámites. Es lo que usa el amigo de tu hermano. |
| Render | Gratis con límites / ~US$21 por mes completo | En el plan gratis la web se duerme a los 15 minutos, no hay worker y la base gratis se borra a los 30 días: no sirve para esto. Pago: `render.yaml` ya está listo. |

La suite está preparada para correr en **un solo proceso** (web + worker que lee GHL y Meta cada 15 minutos) con la base en un archivo (SQLite), así entra en un VPS gratis sin pagar base de datos aparte.

## Pasos (Oracle Cloud)

1. **Cuenta:** crear la cuenta en cloud.oracle.com (región: la más cercana, ej. Bogotá o Ashburn). Esto lo hacés vos.
2. **Servidor:** *Compute › Instances › Create instance* → imagen **Ubuntu 22.04**, forma **VM.Standard.A1.Flex** (Always Free, 1 OCPU y 6 GB alcanzan) → descargar la llave SSH.
3. **Abrir puertos:** en la red de la instancia (*Virtual Cloud Network › Security List*) agregar reglas de entrada TCP **80** y **443** desde `0.0.0.0/0`.
4. **Dominio gratis:** en duckdns.org crear un subdominio (ej. `suite-agencia.duckdns.org`) y apuntarlo a la IP pública del servidor.
5. **Subir el `.env`:** copiar el archivo `.env` de tu compu al servidor en `/opt/suite/.env` (con `scp`).
6. **Instalar:** en el servidor:
   ```bash
   DOMINIO=suite-agencia.duckdns.org REPO=https://github.com/mateobartolome1901/suite-agencia.git bash instalar.sh
   ```
   (el repo es privado: usar una URL con token de solo lectura o una «deploy key» de GitHub).
7. **Login con Google:** en console.cloud.google.com › APIs y servicios › Credenciales › *Crear ID de cliente OAuth* (tipo Aplicación web) con URI de redirección `https://TU-DOMINIO/auth/google/vuelta`. Pegar el ID y el secreto en `/opt/suite/.env` y `sudo systemctl restart suite`.

Actualizar después de un cambio: `cd /opt/suite && git pull && sudo systemctl restart suite`.

## Token de Meta (una sola vez, unos 10 minutos)

**A. Crear la app (si no tenés una):**
1. Entrá a **developers.facebook.com/apps** (con tu usuario de Facebook) › botón **Crear app**.
2. Caso de uso: **Otro** › tipo **Negocios** (Business) › nombre «Suite agencia» › elegí tu portafolio comercial (el Business Manager donde están las cuentas publicitarias) › **Crear app**.

**B. Crear el usuario del sistema y el token:**
1. Entrá directo a **business.facebook.com/settings/system-users** (si te pide elegir portafolio, el mismo de antes).
2. Botón **Agregar** › nombre «suite» › rol **Administrador** › **Crear usuario del sistema**.
3. Con ese usuario seleccionado: **Asignar activos** › **Cuentas publicitarias** › marcá las de Plastia, Realtor Millonario y las de los clientes › permiso **Ver rendimiento** › **Guardar cambios**.
4. Darle la app al usuario: con el mismo usuario seleccionado, **Asignar activos** › **Aplicaciones** › marcá «Suite agencia» › **Control total** (o «Administrar app») › **Guardar cambios**. Sin esto, al generar el token aparece «No hay permisos disponibles». Si la app no figura en la lista: menú izquierdo **Cuentas › Aplicaciones** › **Añadir** › «Conectar un identificador de app» › pegá el ID de la app (está arriba de todo en developers.facebook.com/apps).
5. Botón **Generar token** › elegí la app «Suite agencia» › Caducidad: **Nunca** › marcá **ads_read** y **read_insights** › **Generar token** › **copiar** (se muestra una sola vez).
6. Pegalo en `.env` después de `META_ACCESS_TOKEN=` y guardá. Si otra cuenta publicitaria está en **otro portfolio**, repetí todo en ese portfolio y pegá ese token en `META_ACCESS_TOKEN_2=`: la suite usa para cada cuenta el token que la ve. Probarlo: `python -m servidor.probar`.

Si en el paso B.1 no aparece «Usuarios del sistema»: abrí business.facebook.com › ícono de engranaje (**Configuración**) › menú de la izquierda **Usuarios** › **Usuarios del sistema**.

## Tokens de Go High Level

En cada subcuenta: *Settings › Private Integrations › Create* con permisos: `calendars.readonly`, `calendars/events.readonly`, `contacts.readonly`, `conversations.readonly`, `conversations/message.write` (para responder chats desde la suite). El ID de la subcuenta está en *Settings › Business Profile* (o en la URL: `/location/ESTE_ID/`). Van en `.env`, una línea cada uno: `GHL_PLASTIA_ID=…`, `GHL_PLASTIA_TOKEN=…` (y lo mismo con `GHL_REALTOR_MILLONARIO_…`). Para probarlos: `python -m servidor.probar`.

Después, en la suite: **Ficha de clientes › (la cuenta) › Traer calendarios y campañas** y elegir qué calendarios y qué campañas cuentan para cada negocio (Realtor Millonario tiene cosas que no son de TPA).
