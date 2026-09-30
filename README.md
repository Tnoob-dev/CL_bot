# Cinema Bot 🎬

Bot de Telegram para la gestión y distribución de contenido multimedia (películas, series, anime, juegos y más) con integración a múltiples canales, APIs externas y sistemas de pago.

---

## 📋 Requisitos previos

- Python 3.10+
- PostgreSQL (o SQLite, según configuración)
- Una cuenta de Telegram con API ID y API Hash
- Tokens/API Keys de los servicios utilizados

---

## ⚙️ Configuración del entorno

Todas las variables de entorno deben colocarse en un archivo llamado **`.env`** ubicado en la ruta:

```
bot/core/.env
```

> ⚠️ **Importante:** El archivo `.env` **debe** estar dentro de `bot/core/`, no en la raíz del proyecto. Si el archivo no existe en esa ruta, el bot no podrá cargar la configuración.

### Estructura del archivo `.env`

Crea el archivo `bot/core/.env` con el siguiente contenido y rellena cada valor con tus propias credenciales:

```env
##### BOT #####
NAME=""
TELEGRAM_API_HASH=""
TELEGRAM_API_ID=
TELEGRAM_BOT_TOKEN=""
SENDER_BOT=""

##### ADMIN #####
# IDs de administradores (separados por coma si hay varios)
ADMINS=""

##### CHANNELS #####
# Canal principal de películas
CHANNEL_ID=
# Canal alternativo (opcional, descomentar para usar)
# CHANNEL_ID=

ORDERS_ID=""
CINEMA_ID=""
GROUP_ID=""
GUEST_NAME=""
GUEST_ID=""
GUEST_LINK=""
PAY_GROUP=

##### API KEYS and SECRETS #####
GROQ_KEY=""
OPENSUBTITLES_KEYS=""
OPENSUBTITLE_USERNAME=""
OPENSUBTITLE_PASSWORD=""

##### OTHERS #####
IMDB_API_URL=""
TMDB_API_URL=""
TMDB_IMAGE_BASE_URL=""
OWNER_ID=""
CUP_CARD=""
CUP_CARD2=""
MOBILE=""
Wallet_BEP=""
DELETE_MESSAGE_DELAY=
VIP_PRICE_CUP=
VIP_PRICE_MLC=
VIP_PRICE_USD=
QVAPAY_LINK=""

# Precio de mensajes vía canal
PRICE1=""

# Precio de mensajes vía bot
PRICE2=""

# Precio para canal fijo al bot (unión obligatoria)
PRICE3=""

##### DB #####
# Base de datos principal de cine (PostgreSQL)
POSTGRE_CINE_DB=""

# Base de datos general (PostgreSQL)
POSTGRE_DB_URL=""

# Base de datos de usuarios (PostgreSQL)
USER_DB=""

##### Stream #####
STREAM_BIN_CHANNEL=
STREAM_PORT=
STREAM_URL=""
```

---

## 🔑 Descripción de las variables

### 🤖 BOT
| Variable | Descripción |
|---|---|
| `NAME` | Nombre del bot. |
| `TELEGRAM_API_HASH` | API Hash obtenido en [my.telegram.org](https://my.telegram.org). |
| `TELEGRAM_API_ID` | API ID obtenido en [my.telegram.org](https://my.telegram.org). |
| `TELEGRAM_BOT_TOKEN` | Token del bot generado por [@BotFather](https://t.me/BotFather). |
| `SENDER_BOT` | Username del bot emisor (sin `@`). |

### 🛡️ ADMIN
| Variable | Descripción |
|---|---|
| `ADMINS` | IDs de Telegram de los administradores del bot, separados por coma. |

### 📡 CHANNELS
| Variable | Descripción |
|---|---|
| `CHANNEL_ID` | ID del canal principal donde se publica el contenido. |
| `ORDERS_ID` | Identificador del canal/grupo de pedidos. |
| `CINEMA_ID` | Identificador de la biblioteca de cine. |
| `GROUP_ID` | Identificador del grupo de chat. |
| `GUEST_NAME` | Nombre del usuario invitado. |
| `GUEST_ID` | ID del usuario invitado. |
| `GUEST_LINK` | Enlace al perfil del usuario invitado. |
| `PAY_GROUP` | ID del grupo de pagos. |

### 🔐 API KEYS and SECRETS
| Variable | Descripción |
|---|---|
| `GROQ_KEY` | API Key de [Groq](https://groq.com) para inferencia de IA. |
| `OPENSUBTITLES_KEYS` | Claves de la API de OpenSubtitles (separadas por coma). |
| `OPENSUBTITLE_USERNAME` | Usuario de OpenSubtitles. |
| `OPENSUBTITLE_PASSWORD` | Contraseña de OpenSubtitles. |

### 🧩 OTHERS
| Variable | Descripción |
|---|---|
| `IMDB_API_URL` | URL base de la API de IMDb. |
| `TMDB_API_URL` | URL base de la API de TMDB. |
| `TMDB_IMAGE_BASE_URL` | URL base para las imágenes de TMDB. |
| `OWNER_ID` | ID de Telegram del dueño del bot. |
| `CUP_CARD` / `CUP_CARD2` | Números de tarjeta CUP para pagos. |
| `MOBILE` | Número de teléfono de contacto. |
| `Wallet_BEP` | Dirección de wallet BEP-20 para pagos en cripto. |
| `DELETE_MESSAGE_DELAY` | Tiempo (en segundos) para eliminar mensajes automáticamente. |
| `VIP_PRICE_CUP` | Precio VIP en CUP. |
| `VIP_PRICE_MLC` | Precio VIP en MLC. |
| `VIP_PRICE_USD` | Precio VIP en USD. |
| `QVAPAY_LINK` | Enlace de pago de QvaPay. |
| `PRICE1` | Precio para mensajes vía canal. |
| `PRICE2` | Precio para mensajes vía bot. |
| `PRICE3` | Precio para mensajes en canal fijo al bot (unión obligatoria). |

### 🗄️ DB
| Variable | Descripción |
|---|---|
| `POSTGRE_CINE_DB` | Cadena de conexión a la base de datos principal de cine. |
| `POSTGRE_DB_URL` | Cadena de conexión a la base de datos general. |
| `USER_DB` | Cadena de conexión a la base de datos de usuarios. |

### 📺 Stream
| Variable | Descripción |
|---|---|
| `STREAM_BIN_CHANNEL` | ID del canal binario de streaming. |
| `STREAM_PORT` | Puerto del servidor de streaming. |
| `STREAM_URL` | URL/host del servidor de streaming. |

---

## 🚀 Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd <nombre-del-repositorio>
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crea el archivo `.env` en `bot/core/.env` y completa todas las variables como se indica arriba.

5. Ejecuta el bot:
   ```bash
   python -m bot
   ```

---

## 🔒 Seguridad

- **Nunca** subas el archivo `bot/core/.env` a un repositorio público.
- Añade `bot/core/.env` a tu `.gitignore`.
- Rota las credenciales inmediatamente si sospechas que han sido comprometidas.

Ejemplo de `.gitignore`:
```gitignore
bot/core/.env
.env
venv/
__pycache__/
*.pyc
```