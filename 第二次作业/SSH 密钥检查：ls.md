1. **SSH 密钥**
   检查：`ls ~/.ssh/id_ed25519*`
   生成：`ssh-keygen -a 100 -t ed25519`（

2. **SSH 配置**
   在 `~/.ssh/config` 中写入题目所给的 `Host vm` 配置。

3. **复制公钥**
   运行 `ssh-copy-id vm`。

4. **端口转发验证**
   虚拟机运行 `python -m http.server 8888`，本地浏览器访问 `http://localhost:9999` 能看到文件列表即成功。

5. **SSH 服务安全加固**
   编辑 `/etc/ssh/sshd_config`，设置 `PasswordAuthentication no` 和 `PermitRootLogin no`，然后 `sudo service sshd restart`。

6. **Mosh 挑战**
   Mosh **能**正确恢复连接。它使用 UDP 且设计了连接恢复机制，短暂断网（如断开网卡）后网络恢复时可自动重连。

7. **SSH 参数与后台转发**
   - `-N`：不执行远程命令，用于纯连接（如转发）。
   - `-f`：后台运行 SSH 进程。
   - 后台端口转发命令：`ssh -Nf vm`（利用 config 中的 LocalForward）或 `ssh -Nf -L 9999:localhost:8888 user@host`。