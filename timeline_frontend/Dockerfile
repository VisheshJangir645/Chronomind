# Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
# Use ci for reliable reproducible builds
RUN npm ci

COPY . .
# If you configure React code to rely on backend URL:
# ARG VITE_BACKEND_URL
# ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

RUN npm run build

# Serving Stage
FROM nginx:alpine

# Copy built Vite assets
COPY --from=builder /app/dist /usr/share/nginx/html

# SPA Routing Support: Re-direct all 404s to index.html to allow React Router / standard client routing to function
RUN sed -i 's/location \/ {/location \/ {\n        try_files $uri $uri\/ \/index.html;/' /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
