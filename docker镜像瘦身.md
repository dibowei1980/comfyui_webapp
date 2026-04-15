# Docker 镜像瘦身指南

## 1. 清理 Docker 内部空间

### 1.1 查看磁盘使用情况

```bash
docker system df
```

### 1.2 清理构建缓存

```bash
docker builder prune -af
```

### 1.3 清理未使用的资源

```bash
docker system prune -af --volumes
```

## 2. 压缩 VHDX 虚拟磁盘

### 2.1 执行 fstrim（在 WSL 内释放空间）

确保 Docker Desktop 正在运行：

```powershell
wsl -d docker-desktop -e sh -c "fstrim -v /"
```

### 2.2 设置 VHDX 稀疏属性（推荐）

关闭 Docker Desktop 后执行：

```powershell
wsl --shutdown
wsl --manage docker-desktop --set-sparse true
```

### 2.3 使用 diskpart 压缩（可选）

如果稀疏属性设置后仍需进一步压缩：

```powershell
wsl --shutdown
diskpart
```

在 diskpart 中输入：

```
SELECT VDISK FILE="D:\docker\DockerDesktopWSL\disk\docker_data.vhdx"
ATTACH VDISK READONLY
COMPACT VDISK
DETACH VDISK
EXIT
```

## 3. 完整清理流程

```powershell
# 1. 清理 Docker 缓存
docker builder prune -af
docker system prune -af --volumes

# 2. 执行 fstrim
wsl -d docker-desktop -e sh -c "fstrim -v /"

# 3. 关闭 Docker 并压缩
wsl --shutdown
wsl --manage docker-desktop --set-sparse true
```

## 4. 镜像导出与导入

### 4.1 导出镜像为 tar 文件

```powershell
docker save -o comfyui-server.tar comfyui-server:latest
```

### 4.2 在其他机器导入镜像

```powershell
docker load -i comfyui-server.tar
```

### 4.3 导出后重新标记（可选）

```powershell
docker tag comfyui-server:latest your-registry/comfyui-server:latest
```

## 5. 效果示例

| 操作 | 结果 |
|------|------|
| 清理构建缓存 | 释放 19.16 GB |
| 执行 fstrim | 释放 40 MB |
| 设置稀疏属性 | VHDX 从 27GB 降至 13GB |
| 导出镜像 tar | 镜像 11.8GB → tar 3.76GB |
