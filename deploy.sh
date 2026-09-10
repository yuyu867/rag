#!/usr/bin/env bash
# AI 智能营养师 — 国内服务器一键部署脚本（Ubuntu 22.04）
# 用法：在仓库根目录执行  bash deploy.sh
# 可重复执行，已完成的步骤会自动跳过。
set -e

echo "==> [1/6] 配置 Swap（2G 内存机器必备）"
SWAP_MB=$(free -m | awk '/^Swap:/{print $2}')
if [ "${SWAP_MB:-0}" -lt 1024 ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "    Swap 已开启"
else
  echo "    Swap 已存在，跳过"
fi

echo "==> [2/6] 安装 Docker 引擎（Ubuntu 官方源，阿里云内网直达）"
if command -v docker >/dev/null 2>&1; then
  echo "    已安装：$(docker --version)"
else
  apt-get update -y
  apt-get install -y docker.io
  systemctl enable --now docker
fi

echo "==> [3/6] 安装 docker compose 插件（阿里云镜像池）"
if docker compose version >/dev/null 2>&1; then
  echo "    已安装：$(docker compose version)"
else
  BASE="https://mirrors.aliyun.com/docker-ce/linux/ubuntu/dists/jammy/pool/stable/amd64/"
  F=$(curl -fsSL "$BASE" | grep -o 'docker-compose-plugin_[^"]*amd64\.deb' | sort -V | tail -1)
  echo "    下载 $F"
  curl -fsSL -o /tmp/compose.deb "$BASE$F"
  dpkg -i /tmp/compose.deb
fi

echo "==> [4/6] 配置 Docker Hub 镜像加速（国内拉镜像必备）"
if [ -f /etc/docker/daemon.json ] && grep -q registry-mirrors /etc/docker/daemon.json; then
  echo "    已配置，跳过"
else
  mkdir -p /etc/docker
  cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1ms.run"]
}
EOF
  systemctl restart docker
fi

echo "==> [5/6] 检查 .env 配置"
if [ ! -f .env ]; then
  echo "    ❌ 缺少 .env！请先执行: nano .env"
  echo "       填入 OPENAI_API_KEY / POSTGRES_PASSWORD / JWT_SECRET 后重新运行本脚本"
  exit 1
fi
for k in OPENAI_API_KEY POSTGRES_PASSWORD JWT_SECRET; do
  grep -q "^$k=" .env || { echo "    ❌ .env 缺少 $k"; exit 1; }
done
echo "    .env 校验通过"

echo "==> [6/6] 构建并启动（首次 10-20 分钟，请耐心等待）"
docker compose up -d --build
docker compose ps

echo ""
echo "✅ 部署完成：http://服务器公网IP:8080"
echo "   - 安全组需放行 8080 端口"
echo "   - 默认账户 admin/admin，登录后请立即修改密码"
