#前端镜像

# ---------- 阶段一：构建 ----------
FROM node:24-alpine AS build

WORKDIR /app


# 先只拷贝依赖清单，利用层缓存：package.json 没变就不会重装依赖
COPY frontend/package.json frontend/package-lock.json ./


# npm ci 严格按 package-lock.json 安装，比 npm install 更适合构建
# 【注意】这一步需要能访问 npm registry；离线环境会失败
RUN npm ci

# 再拷贝源码。.dockerignore 已排除 node_modules 与 dist，不会重复拷贝
COPY frontend/ ./

RUN npm run build

# ---------- 阶段二：运行 ----------
FROM nginx:1.27-alpine

#删除官方默认站点，换成本项目的配置
RUN rm -f /etc/nginx/conf.d/default.conf
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 只把上一阶段的构建产物拷过来
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]