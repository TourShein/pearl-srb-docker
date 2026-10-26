# Pearl 专用 SRBMiner 3.8.0 Docker 配方（未实机验证）

这是 **Linux x86-64 + 单张 NVIDIA GPU** 的 runtime-only 配方，不是已经验证的成品镜像。主 Dockerfile **不含矿工二进制**，不自动下载；官方矿工由使用者另行取得并只读挂载。只在自己拥有或获授权的设备上使用。运行环境镜像已于 2026-10-26 在 GitHub Actions 构建成功（run 40272974664，commit 0c372ff）；推送步骤关闭，尚无可拉取的发布镜像。没有执行任何矿工（含 help/version），没有 GPU 实测、挖矿或改主机设置。

## 设计

- 固定 SRBMiner **3.8.0**，只挖 `pearlhash`；禁 CPU、MSR/大页调整和矿工超频。
- 只接收公开 PRL 收款地址；离线检查 `prl1` 的 Bech32/Bech32m 校验及 witness 长度。校验通过不证明地址属于你，也不保证矿池接受该地址类型。**不要填助记词或私钥**。
- 一个完整 GPU UUID；不允许 `all` 或索引。NVIDIA 驱动能力限 `compute,utility`。
- Compose `init: true` 处理 PID 1；不删除容器标识、不伪装环境。非 root、只读根文件系统、临时 tmpfs、去除 capabilities、禁止提权。
- 仅一个用户提供的官方发布目录只读挂载；无 Docker socket、host network、管理 API、公开端口或默认重启。
- TLS 固定开启，使用 SRB 原生 `--tls true`。不设默认矿池/作者钱包/推荐码。参数不通过 eval，不接收任意追加参数。
- 这些隔离不能把闭源矿工变成可信程序；GPU 驱动仍共享宿主内核。矿工可能访问开发费服务，不是“只连接所选矿池”。

## 你手动操作的步骤（以下尚未执行）

需要已有 NVIDIA Linux 主机、兼容驱动、Docker Compose 与已配置的 NVIDIA Container Toolkit。Mac Docker Desktop/本云环境不作为 NVIDIA 实机验证平台。不要为了启动失败直接加 privileged 或关掉隔离。

1. 先创建 `vendor/` 目录，再从[作者 3.8.0 发布页](https://github.com/doktor83/SRBMiner-Multi/releases/tag/3.8.0)自己下载 **SRBMiner-Multi-3-8-0-Linux.tar.gz**，放到 `vendor/`。核对来源和许可，不运行包内脚本。
2. 在本机计算并核对：

```sh
md5sum vendor/SRBMiner-Multi-3-8-0-Linux.tar.gz
sha256sum vendor/SRBMiner-Multi-3-8-0-Linux.tar.gz
cp .env.example .env
```

作者公布的 MD5 是 `01cdd7ffdca43f3b6968fbaacea449b5`。MD5 不能可靠防恶意碰撞；自行算出的 SHA256 只锁定你审查的本地文件，**不是作者签名或独立认证**。本配方没有编造作者 SHA256。可选 Dockerfile.private 同时检查两者；主 runtime-only 镜像没有矿工可校验，由你在宿主核对。

3. 编辑 `.env`：记录本地 SHA256、自己的公开 PRL 地址、worker、一个完整 GPU UUID、所选矿池**当前 TLS hostname/port**。可用宿主 `nvidia-smi -L` 查看 UUID（只读查询）。确认设备授权后把 `MINING_ACK` 改为 `I_OWN_OR_AM_AUTHORIZED_TO_USE_THIS_GPU`。

矿池端口会变，不把 TCP 示例当 SSL 配置。参考 [Kryptex 当前设置页](https://pool.kryptex.com/prl)选择 SSL；它的说明明确 SRB 使用 `--tls true`。此包不替你选择矿池，也不验证 TLS 证书实现或可达性。

4. 核对归档后，在普通用户权限下解压完整官方发布目录到 `vendor/SRBMiner-Multi-3-8-0/`；检查该目录直接包含 `SRBMiner-MULTI`，保留官方附带文件与许可，不运行示例脚本。Compose 只读挂载此目录，缺少目录会报错。再检查配方、手动构建（构建不执行矿工）：

```sh
python3 tests/test_recipe.py
docker compose config --quiet
docker compose build --pull pearl
```

基础镜像 tag 与 apt 软件包并未锁 digest/快照，因此主镜像只固定运行环境版本标签；矿工版本由用户挂载的 3.8.0 官方归档决定，不是完全可复现构建。正式保留镜像前记录已审查的基础镜像 digest；不要把未知 digest 当已验证值。运行环境镜像构建已通过；未验证矿工归档结构、动态库兼容性及实际 GPU 运行。

5. 只有你决定实际用电挖矿时才运行：

```sh
docker compose up pearl
# 另一个终端停止：
docker compose down
```

第一次以前台方式观察，核对 GPU、钱包、TLS 连接、accepted/rejected shares、功耗/温度及矿池统计；看到实际 accepted shares 才算初步运行通过。停止后确认 GPU 负载回落。`restart: "no"` 不阻止矿工内部自己的重试行为。日志滚动限制为 3×10 MB。

## 已知边界与排障

- 未验证 NVIDIA 驱动/CUDA 兼容、显存需求、动态库、真实 TLS、份额、性能、开发费、信号退出或只读文件系统兼容性。
- `--autotune-no-load` 避免自动读写调优文件；HOME/工作目录在 tmpfs。若日志仍报只读写入失败，应定位所需路径后审查最小调整，不能默认全盘可写。
- `tmpfs noexec` 或非 root 如与闭源程序冲突，此版本会失败；不要自动放宽权限。若矿工拒绝容器，记录错误并停止，不隐藏 `/.dockerenv`。
- Tini/init 解决的是 PID 1 管理问题，不证明所有 SRB 版本支持容器。此包没有修补/绕过矿工检查。
- 本包不提供自动调频、功率限制、温度关机或重启主机脚本。不套用其他 GPU/版本的超频参数。
- 作者对预编译 GPU 二进制的许可有限制；主镜像不含矿工；可选 `Dockerfile.private` 仅提供私有构建配方，**不要推送包含矿工的镜像或再分发归档**，需要分发时先确认作者书面许可。私有构建也不等于本说明替你取得许可。

来源见 `SOURCES.md`，验证范围见 `VALIDATION.md`。

## 仓库 / CI 发布

`.github/workflows/runtime-image.yml` 只支持人工 `workflow_dispatch`，默认 `publish=false`：mock 测试后构建主 Dockerfile。显式选 `publish=true` 才用仓库内置 GITHUB_TOKEN 推送到 `ghcr.io/<owner>/<repo>` 的 `runtime-3.8.0` 与 commit 标签。**这是 GHCR，不是 Google gcr.io**；实际发布目标应先确定。没有 push 自动触发，没有 GPU runner，没有矿工运行步骤。官方 checkout 使用 v4 大版本引用，正式强化供应链时可锁已审查 commit。GitHub runner 是否产生费用取决于账户额度/仓库设置；已运行一次仅构建 CI 并成功，未推送镜像。

`.dockerignore` 把 `vendor` 与 `.env` 排除在主构建上下文之外；`.gitignore` 防止误提交官方文件。发布前仍需检查 git diff。CI 构建/推送成功也不代表有 GPU 的实际挖矿通过。

如要**仅本地私有**封装完整归档：`docker build -f Dockerfile.private --build-arg SRB_SHA256=<本地核对的SHA256> -t pearl-srb-private:3.8.0 .`；专用 ignore 文件允许此私有构建读取归档。不要用 CI 发布该 Dockerfile。
