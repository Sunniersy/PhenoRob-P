ARG BASE_IMAGE_NODE=robot-cloud-node-base:20-alpine
ARG BASE_IMAGE_NGINX=robot-cloud-nginx-base:1.27-alpine

FROM ${BASE_IMAGE_NODE} AS build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM ${BASE_IMAGE_NGINX}
COPY deploy/frontend.nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
