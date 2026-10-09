# Docker 全栈部署

项目由 Vue/Vite 前端、FastAPI 后端和后台 worker 组成，依赖 MySQL、Redis、RabbitMQ 与 MinIO。Docker Compose 会构建前后端镜像，并为有状态服务创建持久化卷。

## 首次部署

1. 安装 Docker Engine 和 Docker Compose 插件。
2. 将 `.env.example` 复制为 `.env`，为数据库、Redis、RabbitMQ、MinIO、JWT 和管理员账号填写独立的随机值。密码请使用字母与数字，避免连接 URL 中的特殊字符需要额外编码。
3. 执行：

   ```sh
   docker compose up -d --build
   ```

4. 浏览器打开 `http://localhost:8080`。初始管理员账号由 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 设置。

验证部署时可打开 `http://localhost:8080/health` 查看 API 健康状态，打开 `http://localhost:8080/api/v1/docs` 查看接口文档；`docker compose ps` 会显示各容器的健康状态。

首次启动会等待 MySQL 就绪，然后幂等地建表、初始化角色和管理员，并执行奖品每日上限字段迁移。API 与 worker 在初始化成功后启动。

## 常用命令

```sh
docker compose ps
docker compose logs -f backend worker
docker compose down
```

`docker compose down` 会保留数据库、队列和对象存储数据。删除所有数据前，需明确删除对应的 Docker 卷；生产环境应先备份。

## 对外访问与配置

- 默认只向宿主机发布前端 `8080` 端口。设置 `APP_PORT` 可更改入口端口。
- `/api/` 与 `/health` 由 Nginx 转发到 FastAPI；`/storage/` 转发到 MinIO，因此图片使用与页面相同的域名。
- 通过域名或 HTTPS 反向代理访问时，将 `.env` 中 `MINIO_PUBLIC_URL` 改为 `https://你的域名/storage`，并按需调整 `APP_PORT`。
- MySQL、Redis、RabbitMQ 和 MinIO API 不直接映射到宿主机端口，只在 Compose 内部网络提供服务。
- 首次部署如需镜像仓库代理或离线镜像，需先准备相应镜像；前端构建阶段还需要 npm registry 可用。
