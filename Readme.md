# 🔐 Auth System - Sistema de Autenticación

Un sistema robusto de autenticación construido con **FastAPI**, diseñado como barrera de seguridad para servicios microservicios. Proporciona gestión completa de usuarios, autenticación JWT, control de roles y protección contra ataques.

## 📋 Tabla de Contenidos

- [Objetivo del Proyecto](#objetivo-del-proyecto)
- [Características](#características)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [Endpoints Principales](#endpoints-principales)
- [Arquitectura](#arquitectura)
- [Seguridad](#seguridad)

---

## 🎯 Objetivo del Proyecto

Este proyecto es un **servidor de autenticación centralizado** que actúa como gateway de seguridad para una arquitectura de microservicios. Sus responsabilidades principales son:

1. **Autenticación de Usuarios**: Registro, login y verificación de identidad
2. **Gestión de Tokens**: Emisión de access_tokens y refresh_tokens con seguridad JWT
3. **Control de Acceso**: Sistema de roles y permisos para autorización
4. **Integración de Email**: Coordinación con servicio de envío de correos para verificación
5. **Seguridad**: Protección contra fuerza bruta, lista negra de tokens, validación de email
6. **Cache**: Almacenamiento en Redis para sesiones y bloqueos de seguridad

---

## ✨ Características

- ✅ **Autenticación JWT** con access_token y refresh_token
- ✅ **Verificación de Email** obligatoria en el registro
- ✅ **Sistema de Roles y Permisos** granulares
- ✅ **Protección contra Fuerza Bruta** (bloqueo temporal tras múltiples intentos fallidos)
- ✅ **Lista Negra de Tokens** en Redis para logout seguro
- ✅ **Middleware de Autenticación** que valida tokens en cada petición
- ✅ **Integración con Email-Service** para envío de correos de verificación
- ✅ **Migraciones de Base de Datos** con Alembic
- ✅ **Tareas Asincrónicas** con Celery
- ✅ **Cache con Redis** para optimización y seguridad
- ✅ **Documentación Automática** con Swagger UI

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.10+
- PostgreSQL
- Redis
- Git

### Pasos de Instalación

```bash
# 1. Clonar o navegar al proyecto
cd auth_sys

# 2. Crear ambiente virtual
python -m venv venv

# 3. Activar ambiente virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear archivo .env (copiar desde .env.example)
cp .env.example .env
```

---

## 🛠️ Configuración

### Variables de Entorno (`.env`)

```env
# ===== BASE DE DATOS =====
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/auth_db

# ===== JWT =====
SECRET_KEY=tu-clave-secreta-muy-larga-y-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_MINUTES=43200

# ===== REDIS =====
REDIS_URL=redis://localhost:6380/0

# ===== EMAIL SERVICE =====
EMAIL_SERVICE_URL=http://localhost:8002
EMAIL_SERVICE_TIMEOUT=10

# ===== AUTH SERVICE =====
AUTH_SERVICE_URL=http://localhost:8000

# ===== CELERY =====
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# ===== OPCIONALES =====
DEBUG=False
LOG_LEVEL=INFO
```

### Inicializar Base de Datos

```bash
# Ejecutar las migraciones
alembic upgrade head

# Si necesitas crear una nueva migración después de cambios en modelos:
alembic revision --autogenerate -m "Descripción del cambio"
alembic upgrade head
```

---

## ▶️ Ejecución

### Terminal 1: Celery Worker (Para tareas asincrónicas)

```bash
# Importante: Especificar la cola "auth_tasks"
celery -A src.core.celery_app worker --queue auth_tasks --loglevel=info --pool=solo
```

### Terminal 2: Servidor FastAPI

```bash
# Con recarga automática en desarrollo
uvicorn src.main:app --reload --port 8000

# Producción
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Acceder a la API

- **Swagger UI (Documentación Interactiva)**: http://localhost:8000/docs
- **ReDoc (Documentación Alternativa)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 📡 Endpoints Principales

### Autenticación

| Método | Endpoint | Descripción | Requiere Auth |
|--------|----------|-------------|---------------|
| `POST` | `/auth/register` | Registrar nuevo usuario | ❌ |
| `GET` | `/auth/verify-email` | Verificar correo con token | ❌ |
| `POST` | `/auth/login` | Iniciar sesión | ❌ |
| `POST` | `/auth/refresh` | Refrescar access_token | ❌ |
| `POST` | `/auth/logout` | Cerrar sesión | ✅ |

### Usuarios

| Método | Endpoint | Descripción | Requiere Auth |
|--------|----------|-------------|---------------|
| `GET` | `/users/me` | Obtener perfil del usuario actual | ✅ |
| `PUT` | `/users/{user_id}` | Actualizar usuario | ✅ |
| `DELETE` | `/users/{user_id}` | Eliminar usuario | ✅ |
| `GET` | `/users` | Listar todos los usuarios | ✅ |

### Roles

| Método | Endpoint | Descripción | Requiere Auth |
|--------|----------|-------------|---------------|
| `GET` | `/roles` | Listar todos los roles | ✅ |
| `POST` | `/roles` | Crear nuevo rol | ✅ |
| `POST` | `/roles/{role_id}/assign` | Asignar rol a usuario | ✅ |

### Ejemplos de Uso

```bash
# 1. Registrar usuario
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan_perez",
    "email": "juan@example.com",
    "password": "SecurePassword123!"
  }'

# 2. Verificar email (usar el token enviado por correo)
curl -X GET "http://localhost:8000/auth/verify-email?token=TOKEN_DEL_EMAIL"

# 3. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@example.com",
    "password": "SecurePassword123!"
  }'

# Respuesta:
# {
#   "access_token": "eyJhbGc...",
#   "refresh_token": "abcd1234...",
#   "token_type": "bearer"
# }

# 4. Usar el access_token en peticiones protegidas
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 5. Refrescar token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token"
  }'

# 6. Logout (invalida el token en Redis)
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token"
  }'
```

---

## 🏗️ Arquitectura

### Estructura del Proyecto

```
src/
├── main.py                          # Punto de entrada de FastAPI
├── common/
│   ├── middleware/                  # Middleware personalizado
│   │   └── token_blacklist.py       # Valida tokens en lista negra
│   ├── auth/                        # Autenticación
│   │   ├── dependencies.py          # Dependencias de inyección
│   │   ├── token.py                 # Lógica de JWT
│   │   └── user.py                  # Obtención de usuario actual
│   ├── exceptions/                  # Excepciones personalizadas
│   ├── response/                    # Esquemas de respuesta
│   └── models.py                    # Modelos compartidos
├── core/
│   ├── config.py                    # Configuración (variables env)
│   ├── cache.py                     # Cliente Redis
│   ├── database.py                  # Configuración PostgreSQL
│   ├── email.py                     # Integración con Email Service
│   └── celery_app.py                # Configuración Celery
├── manager/
│   ├── models/                      # Modelos SQLModel
│   │   ├── user.py
│   │   └── token.py
│   ├── schemas/                     # Schemas Pydantic
│   │   ├── user.py
│   │   └── auth.py
│   ├── services/                    # Lógica de negocio
│   │   ├── auth.py                  # Servicio de autenticación
│   │   ├── user.py
│   │   └── role.py
│   └── routes/                      # Rutas/Endpoints
│       ├── auth.py
│       ├── user.py
│       └── role.py
├── tasks/
│   └── email_tasks.py               # Tareas Celery
└── utils/
    ├── security.py                  # Hash de contraseñas
    ├── email.py                     # Utilidades de email
    ├── validation.py                # Validaciones personalizadas
    └── strings.py                   # Utilidades de strings
```

### Flujo de Autenticación

```
1. Usuario → POST /auth/register
   ↓
2. Generar token de verificación de email
   ↓
3. Enviar correo a través de Email-Service (Celery task)
   ↓
4. Usuario → GET /auth/verify-email?token=...
   ↓
5. Marcar email como verificado en BD
   ↓
6. Usuario → POST /auth/login (email+password)
   ↓
7. Generar JWT access_token (15 min) + refresh_token (30 días)
   ↓
8. Usuario usa access_token en header Authorization: Bearer
   ↓
9. Middleware TokenBlacklistMiddleware valida token no esté en blacklist
   ↓
10. Petición autorizada
```

### Flujo de Logout

```
1. Usuario → POST /auth/logout (con access_token + refresh_token)
   ↓
2. Revocar refresh_token en BD (marcar como revoked)
   ↓
3. Agregar access_token a blacklist en Redis (con TTL = exp time)
   ↓
4. Próximas peticiones con ese token serán rechazadas por middleware
```

---

## 🔐 Seguridad

### Medidas Implementadas

1. **Contraseñas**: Hash con bcrypt + salt
2. **Tokens JWT**: Firmados con clave secreta, no contienen contraseñas
3. **HTTPS**: Campo para SSL/TLS en configuración
4. **CORS**: Puede configurarse en `main.py` para restringir orígenes
5. **Rate Limiting**: Protección contra fuerza bruta en login
   - Máximo 5 intentos fallidos por email
   - Máximo 5 intentos fallidos por IP
   - Bloqueo temporal de 5 minutos
6. **Token Blacklist**: Redis guarda tokens revocados al logout
7. **Email Verification**: Requisito obligatorio antes de primer login
8. **Refresh Token Rotation**: Tokens de refresco se pueden revocar
9. **SQL Injection Prevention**: SQLModel + SQLAlchemy ORM
10. **CSRF Protection**: FastAPI incluye soporte integrado

### Recomendaciones de Seguridad para Producción

```python
# 1. Siempre usar HTTPS
# 2. Usar variables secretas en .env (nunca en código)
# 3. Configurar CORS restrictivamente
# 4. Cambiar SECRET_KEY regularmente
# 5. Mantener dependencias actualizadas
# 6. Usar contraseñas fuertes en BD y Redis
# 7. Monitorear intentos fallidos de login
# 8. Implementar 2FA (Two-Factor Authentication)
# 9. Usar Redis con autenticación
# 10. Configurar logs y alertas
```

---

## 📚 Dependencias Principales

| Paquete | Versión | Propósito |
|---------|---------|----------|
| FastAPI | 0.121+ | Framework web asincrónico |
| SQLModel | Latest | ORM y validación combinadas |
| python-jose | Latest | Manejo de JWT |
| passlib | Latest | Hashing de contraseñas |
| bcrypt | Latest | Algoritmo de hashing seguro |
| redis | Latest | Cache y broker Celery |
| celery | 5.5+ | Tareas asincrónicas |
| alembic | Latest | Migraciones de BD |
| pydantic | 2.0+ | Validación de datos |
| httpx | Latest | Cliente HTTP asincrónico |

---

## 🐛 Troubleshooting

### Error: "Could not connect to Redis"
```bash
# Verificar que Redis está corriendo
redis-cli ping  # Debe retornar PONG

# Si no está corriendo:
# Windows: redis-server
# Linux: redis-server o systemctl start redis
```

### Error: "database connection refused"
```bash
# Verificar que PostgreSQL está corriendo
# Y que la DATABASE_URL es correcta en .env
# Verificar puerto (default: 5432)
```

### Error: "Token invalid or missing"
```bash
# 1. Verificar que incluyes el header Authorization
# 2. Verificar que el token no ha expirado (access_token = 15 min)
# 3. Usar refresh endpoint para obtener nuevo access_token
```

### Celery tasks no se ejecutan
```bash
# 1. Verificar que celery worker está corriendo
# 2. Verificar que usa la cola correcta: --queue auth_tasks
# 3. Verificar que Redis está disponible
# 4. Revisar logs de celery
```

---

## 📞 Integración con Email-Service

Este proyecto se integra con **email-service** para enviar correos de verificación. Ver la documentación del repos email-service para detalles.

**Punto de integración**:
- `src/tasks/email_tasks.py` - Envía tareas Celery
- `src/core/email.py` - Cliente HTTP para Email-Service
- Endpoint: `POST /email/send` en email-service

---

## 📄 Licencia

MIT License - Puedes usar este código libremente

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

## 📞 Contacto & Soporte

Para reportar bugs o sugerencias, abre un issue en el repositorio.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/HEAM275/authentication-sys)

**Última actualización**: 15 de febrero de 2026
