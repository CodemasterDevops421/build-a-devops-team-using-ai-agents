# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS build
WORKDIR /frontend

COPY package.json package-lock.json* .
RUN if [ -f package-lock.json ]; then npm ci; else npm install --package-lock-only && npm ci; fi

COPY . .

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN VITE_API_BASE_URL=$VITE_API_BASE_URL npm run build

FROM nginx:1.25-alpine
COPY --from=build /frontend/dist /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
