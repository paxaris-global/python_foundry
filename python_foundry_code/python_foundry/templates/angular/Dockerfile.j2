FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /tmp/dist
RUN APP_DIR="$(ls -1 /tmp/dist | head -n 1)" && cp -r "/tmp/dist/${APP_DIR}/." /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
