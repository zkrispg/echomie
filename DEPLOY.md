# EchoMie 部署指南

## 架构概览

```
用户浏览器
    │
    ▼ (80/443)
┌─────────┐     ┌──────────┐     ┌───────────┐
│  Nginx   │────▶│ FastAPI  │────▶│ PostgreSQL│
│ (前端+   │     │ Backend  │     └───────────┘
│  反向代理)│     └────┬─────┘
└─────────┘          │          ┌───────────┐
                     ├─────────▶│   Redis   │
                     │          └─────┬─────┘
                ┌────┴─────┐         │
                │  Worker  │◀────────┘
                │ (任务处理) │
                └──────────┘
```

- **Nginx**: 提供前端静态文件 + 反向代理 API 请求
- **Backend**: FastAPI + Gunicorn (4 workers)
- **Worker**: 后台消费 Redis 队列, 执行卡通化处理
- **PostgreSQL**: 持久化数据
- **Redis**: 任务队列 + 密码重置码缓存

---

## 方案一: 云服务器部署 (推荐)

### 1. 购买云服务器

推荐配置:

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU  | 2 核    | 4 核    |
| 内存 | 4 GB    | 8 GB    |
| 硬盘 | 50 GB SSD | 100 GB SSD |
| 带宽 | 3 Mbps  | 5 Mbps  |
| 系统 | Ubuntu 22.04 / Debian 12 | Ubuntu 22.04 |

推荐平台:
- **阿里云 ECS**: https://www.aliyun.com/product/ecs
- **腾讯云 CVM**: https://cloud.tencent.com/product/cvm
- **华为云 ECS**: https://www.huaweicloud.com/product/ecs.html
- **AWS EC2** / **Google Cloud** (海外用户)

### 2. 安装 Docker

SSH 登录服务器后执行:

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 启动 Docker
sudo systemctl enable docker
sudo systemctl start docker

# 安装 Docker Compose (新版 Docker 已自带)
docker compose version

# 将当前用户加入 docker 组 (免 sudo)
sudo usermod -aG docker $USER
# 重新登录生效
```

### 3. 上传代码

```bash
# 方法 A: Git
git clone https://your-repo-url.git /opt/echomie
cd /opt/echomie

# 方法 B: SCP 直接上传
scp -r ./backend ./frontend ./docker-compose.prod.yml .env.production deploy.sh root@YOUR_IP:/opt/echomie/
ssh root@YOUR_IP
cd /opt/echomie
```

### 4. 配置环境变量

```bash
cd /opt/echomie
cp .env.production .env

# 生成安全密钥
JWT_KEY=$(openssl rand -hex 32)
INTERNAL_KEY=$(openssl rand -hex 16)
DB_PASS=$(openssl rand -base64 24)
REDIS_PASS=$(openssl rand -base64 24)

# 写入 .env
sed -i "s/CHANGE_ME_USE_STRONG_PASSWORD/$DB_PASS/" .env
sed -i "s/CHANGE_ME_REDIS_PASSWORD/$REDIS_PASS/" .env
sed -i "s/CHANGE_ME_GENERATE_WITH_OPENSSL/$JWT_KEY/" .env
sed -i "s/CHANGE_ME_INTERNAL_TOKEN/$INTERNAL_KEY/" .env

# 确认
cat .env
```

### 5. 一键部署

```bash
chmod +x deploy.sh
bash deploy.sh
```

部署完成后访问: `http://YOUR_SERVER_IP`

### 6. 查看日志

```bash
# 所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 仅后端
docker compose -f docker-compose.prod.yml logs -f backend

# 仅 worker
docker compose -f docker-compose.prod.yml logs -f worker
```

---

## 方案二: 绑定域名 + HTTPS

### 1. 购买域名

- 阿里云万网: https://wanwang.aliyun.com
- 腾讯云 DNSPod: https://dnspod.cloud.tencent.com
- Cloudflare (海外): https://www.cloudflare.com

### 2. DNS 解析

在域名控制台添加 A 记录:
- 主机记录: `@` 或 `echomie`
- 记录类型: A
- 记录值: 你的服务器 IP

### 3. 申请 SSL 证书 (Let's Encrypt 免费)

```bash
# 安装 certbot
sudo apt install certbot -y

# 先停止占用 80 端口的服务
docker compose -f docker-compose.prod.yml down

# 申请证书 (替换 YOUR_DOMAIN)
sudo certbot certonly --standalone -d YOUR_DOMAIN

# 证书位置:
#   /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem
#   /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem
```

### 4. 使用 HTTPS Nginx 配置

```bash
# 编辑 nginx-ssl/nginx.conf, 把 YOUR_DOMAIN 替换为你的域名
sed -i 's/YOUR_DOMAIN/echomie.example.com/g' nginx-ssl/nginx.conf

# 在 docker-compose.prod.yml 的 frontend service 中:
# 1. 映射 443 端口
# 2. 挂载证书目录
```

在 `docker-compose.prod.yml` 的 frontend 部分修改为:

```yaml
  frontend:
    build: ./frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - ./nginx-ssl/nginx.conf:/etc/nginx/conf.d/default.conf:ro
```

### 5. 自动续签

```bash
# 添加 crontab 自动续签 (每月 1 号凌晨 3 点)
echo "0 3 1 * * certbot renew --quiet && docker compose -f /opt/echomie/docker-compose.prod.yml restart frontend" | sudo crontab -
```

---

## 常用运维命令

```bash
# 更新代码后重新部署
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 仅重启某个服务
docker compose -f docker-compose.prod.yml restart backend

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 进入后端容器调试
docker compose -f docker-compose.prod.yml exec backend bash

# 备份数据库
docker compose -f docker-compose.prod.yml exec db pg_dump -U echomie echomie > backup.sql

# 恢复数据库
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U echomie echomie

# 清理未使用的镜像
docker system prune -f
```

---

## 文件结构

```
echomie/
├── backend/                  # FastAPI 后端
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py
│   │   ├── effects.py        # 卡通化处理引擎
│   │   └── ...
│   ├── worker.py
│   └── requirements.txt
├── frontend/                 # React 前端
│   ├── Dockerfile
│   ├── nginx.conf            # Nginx 配置 (HTTP)
│   └── src/
├── nginx-ssl/
│   └── nginx.conf            # Nginx 配置 (HTTPS)
├── docker-compose.prod.yml   # 生产编排
├── .env.production           # 环境变量模板
├── deploy.sh                 # 一键部署脚本
└── DEPLOY.md                 # 本文档
```

---

## 注意事项

1. **安全**: 务必修改所有 `CHANGE_ME` 密码, 不要使用默认值
2. **备份**: 定期备份 PostgreSQL 数据和 `/data/storage` 目录
3. **监控**: 建议接入 UptimeRobot 等免费监控, 监控 `http://YOUR_DOMAIN/ping`
4. **扩容**: 如需处理更多并发, 增加 worker replicas:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --scale worker=3
   ```
5. **国内备案**: 如果域名指向国内服务器, 需要先完成 ICP 备案
