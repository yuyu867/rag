# 前端镜像：Node 构建 → nginx 托管静态文件并反代 /api
# ---------- 构建阶段 ----------
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
# 国内 npm 镜像，海外部署可删掉 config set 这行
RUN npm config set registry https://registry.npmmirror.com && npm install

COPY . .
# vue-tsc 类型检查 + vite 构建
RUN npm run build

# ---------- 运行阶段 ----------
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
