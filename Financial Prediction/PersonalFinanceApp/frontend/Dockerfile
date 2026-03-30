# -----------------------------------------------------------------------------
# Stage 1 — build React (Vite) app
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.ts tsconfig.json tsconfig.node.json ./
COPY src ./src

RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2 — nginx serves dist + admin portal
# -----------------------------------------------------------------------------
FROM nginx:alpine
WORKDIR /usr/share/nginx/html

COPY --from=builder /app/dist ./
COPY admin/ ./admin/
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
