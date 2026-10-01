# Community Frontend

## Variables de entorno

Copia `.env.example` como `.env`:

```bash
cp .env.example .env
```

Configura el mismo valor de `API_KEY` que usa el backend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=local-community-api-key-change-me
NEXT_PUBLIC_WHATSAPP_URL=https://chat.whatsapp.com/tu-enlace
NEXT_PUBLIC_INSTAGRAM_URL=https://instagram.com/tu-cuenta
NEXT_PUBLIC_MEETUP_URL=https://meetup.com/tu-grupo
NEXT_PUBLIC_TELEGRAM_URL=https://t.me/tu-canal-de-consultas
NEXT_PUBLIC_LINKEDIN_URL=https://linkedin.com/company/tu-organizacion
```

El frontend envía la key en el header `X-API-Key` en cada petición al backend.

## Desarrollo

```bash
pnpm install
pnpm dev
```

## Docker

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  --build-arg NEXT_PUBLIC_API_KEY=local-community-api-key-change-me \
  -t community-frontend .
docker run --rm -p 3000:3000 community-frontend
```