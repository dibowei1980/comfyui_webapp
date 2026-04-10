完整解决方案：

1. 启动 Docker Desktop （让 WSL 实例运行）
2. 在管理员 PowerShell 中执行：
   ```
   # 进入 WSL Docker 实例执行 fstrim
   wsl -d docker-desktop -e sh -c 
   "fstrim -v /mnt/
   docker-desktop-disk/data"
   ```
3. 关闭 Docker Desktop
4. 再次执行压缩：
   ```
   wsl --shutdown
   diskpart
   # 然后输入:
   select vdisk 
   file="D:\docker\DockerDesktopWSL\
   disk\docker_data.vhdx"
   compact vdisk
   exit
   ```
   <br />

