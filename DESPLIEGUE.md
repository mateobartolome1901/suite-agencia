# Publicar la suite gratis

## Qué conviene

| Opción | Costo | Qué pasa |
|---|---|---|
| **Google Cloud e2-micro (nivel gratis)** — elegido | US$0 dentro del nivel gratis | Un servidor chico (2 núcleos compartidos, 1 GB + 2 GB de respaldo en disco): alcanza para la suite. Pide tarjeta. Crear presupuesto de US$1 con alerta. |
| VPS gratis de Oracle Cloud (Always Free) — rechazó la tarjeta | US$0 para siempre | Un servidor propio (hasta 4 núcleos y 24 GB): corre la suite y el worker juntos, siempre prendido. Pide tarjeta solo para verificar identidad; no cobra si usás lo «Always Free». |
| VPS barato (Hetzner, Contabo) | ~US$4–6 por mes | Plan B si Google falla: más rápido, sin trámites. Es lo que usa el amigo de tu hermano. |
| Render | Gratis con límites / ~US$21 por mes completo | En el plan gratis la web se duerme a los 15 minutos, no hay worker y la base gratis se borra a los 30 días: no sirve para esto. Pago: `render.yaml` ya está listo. |

La suite está preparada para correr en **un solo proceso** (web + worker que lee GHL y Meta cada 15 minutos) con la base en un archivo (SQLite), así entra en un VPS gratis sin pagar base de datos aparte.

## Pasos (Google Cloud, gratis)

1. **Cuenta:** console.cloud.google.com con mateobartolome1901@gmail.com › aceptar términos › **Probar gratis / Activar** (país, tarjeta). Te dan US$300 de prueba por 90 días; el servidor e2-micro sigue gratis después.
2. **Proyecto:** arriba a la izquierda, selector de proyecto › **Proyecto nuevo** › nombre `suite-agencia` › Crear (y dejarlo elegido).
3. **Alerta de gasto:** menú ☰ › **Facturación** › **Presupuestos y alertas** › Crear presupuesto › US$1 › alertas al 50 %, 90 % y 100 % (te avisa por mail si algo empezara a cobrarse).
4. **Servidor:** menú ☰ › **Compute Engine › Instancias de VM** (si pide, **Habilitar** la API) › **Crear instancia**:
   - Nombre `suite`; región **us-east1 (Carolina del Sur)** (o us-central1 / us-west1: solo esas tres son gratis).
   - Configuración de máquina: serie **E2**, tipo **e2-micro**.
   - SO y almacenamiento › **Cambiar**: **Ubuntu 22.04 LTS (x86/64)**, tipo de disco **Disco persistente estándar** (no «equilibrado»: ese cobra), **30 GB**.
   - Redes: marcar **Permitir tráfico HTTP** y **Permitir tráfico HTTPS**.
   - **Crear**. Anotar la **IP externa**.
5. **IP fija:** menú ☰ › **Red de VPC › Direcciones IP** › en la IP de `suite` › **Promover a dirección IP estática** (si no, cambia al reiniciar).
6. Seguir desde el paso 4 de abajo (DuckDNS). Para entrar al servidor: en la lista de instancias, botón **SSH** (abre una consola en el navegador).

## Pasos (Oracle Cloud, alternativa)

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
