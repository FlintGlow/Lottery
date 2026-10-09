# 幸运抽奖系统

一个用于活动运营的全栈抽奖系统，提供活动浏览与抽奖、中奖记录和领奖管理，以及面向运营人员的管理后台。

## 功能

- 活动管理：创建和维护抽奖活动及活动状态。
- 奖品管理：维护奖品、库存和抽奖配置。
- 抽奖处理：通过 Redis 和 RabbitMQ 支持抽奖请求处理，并由后台 worker 消费抽奖结果、执行补偿和活动状态检查。
- 中奖与领奖：查看中奖记录，管理领奖信息和兑奖进度。
- 运营管理：用户与角色管理、数据统计和操作记录。
- 图片存储：使用 MinIO 保存上传文件。

## 技术栈

| 部分 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Pinia |
| 后端 API | Python、FastAPI、SQLAlchemy（异步） |
| 数据库 | MySQL 8 |
| 缓存 | Redis 7 |
| 消息队列 | RabbitMQ |
| 对象存储 | MinIO |
| 部署 | Docker Compose、Nginx |

## 快速启动

### 使用 Docker Compose（推荐）

需要安装 Docker Engine 和 Docker Compose 插件。在项目根目录执行：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，为数据库、Redis、RabbitMQ、MinIO 和 JWT 配置独立的随机密码或密钥，并设置管理员账号密码。然后启动服务：

```sh
docker compose up -d --build
```

启动后访问：

- 前端：<http://localhost:8080>
- API 健康检查：<http://localhost:8080/health>
- API 文档：<http://localhost:8080/api/v1/docs>

初始管理员账号由 `.env` 中的 `ADMIN_USERNAME`、`ADMIN_PASSWORD` 和 `ADMIN_PHONE` 设置。默认入口端口为 `8080`，可通过 `APP_PORT` 修改。

常用命令：

```sh
docker compose ps
docker compose logs -f backend worker
docker compose down
```

Compose 会将数据库、队列和对象存储数据保存在 Docker 卷中；普通的 `docker compose down` 不会删除这些数据。完整部署配置、远程访问和存储说明见 [DOCKER.md](DOCKER.md)。

## 项目结构

```text
.
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由
│   │   ├── core/         # 配置、数据库、缓存、消息队列和对象存储
│   │   ├── models/       # 数据模型
│   │   ├── repositories/ # 数据访问
│   │   ├── schemas/      # 请求与响应模型
│   │   ├── services/     # 业务逻辑
│   │   └── tasks/        # 异步 worker 与后台任务
│   └── scripts/          # 管理员初始化和数据迁移脚本
├── frontend/
│   └── src/
│       ├── api/          # API 客户端
│       ├── components/   # 通用组件
│       ├── router/       # 前端路由
│       ├── stores/       # Pinia 状态
│       └── views/        # 页面与管理后台
├── docker-compose.yaml
├── .env.example
└── DOCKER.md
```

## 本地开发

前端使用 Node.js `^22.18.0` 或 `>=24.12.0`。进入 `frontend` 目录安装依赖并启动 Vite：

```sh
npm install
npm run dev
```

后端依赖见 `backend/requirements.txt`，入口为 `backend/app/main.py`。本地运行 API 还需要 MySQL、Redis、RabbitMQ 和 MinIO，并在后端环境中设置对应连接地址及 `CORS_ORIGINS`。开发环境的具体部署和配置可参考 [DOCKER.md](DOCKER.md) 与 `.env.example`。
