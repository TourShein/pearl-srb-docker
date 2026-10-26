# Pearl / SRBMiner：Unraid 拉取运行

**候选版本：`ghcr.io/tourshein/pearl-srb-docker:bootstrap-3.8.0`。本文件不代表镜像已发布；发布成功且包设为 Public 后才支持匿名 pull。尚未做真实 GPU / Unraid 挖矿验证。**

这个镜像不是空壳手工装矿工：镜像带运行库与启动器，**你第一次启动时自动从原作者下载 SRBMiner 3.8.0，校验固定 SHA256，然后执行挖矿**。后续启动复用专用缓存，不需再手动下载/挂载矿工。镜像层不打包或再分发闭源矿工。

## 两步启动

前提：x86-64 Unraid，已配置可用的 NVIDIA 驱动和容器 GPU 支持，Docker Compose 支持 GPU `device_ids`。只用你有权使用的硬件。需要先取得自己的 Pearl **公开收款地址**，不填助记词或私钥。

1. 将本仓库 `compose.yaml` 和 `.env.example` 放在一个新配置目录。复制 `.env.example` 为 `.env`，只改这两项：
   ```dotenv
   PRL_WALLET=你的有效prl1公开收款地址
   GPU_UUID=GPU-你的完整显卡UUID
   ```
   UUID 可在 Unraid 终端用 `nvidia-smi -L` 查看；不要填 `all` 或卡序号。默认 worker `pearl01`，默认 Kryptex TLS `prl.kryptex.network:8048`。Compose 会把同一个 UUID 同时用于 GPU reservation 和 NVIDIA_VISIBLE_DEVICES。
2. **此命令会下载并执行闭源挖矿软件，产生电耗和费用；确认上游许可及风险后由你自行执行：**
   ```sh
   docker compose pull && docker compose up -d
   ```
   看日志：`docker compose logs -f --tail=100 pearl`。停止：`docker compose down`。

第一次启动需要网络访问 GitHub 发布资源及其重定向下载域名。没有有效钱包/UUID会在下载前退出；下载、校验或解包失败也会停止，不尝试其他版本/镜像。后续仍需连接矿池及矿工开发者费服务。

## 实际包含什么 / 费用

- 镜像：CUDA 12.9 / Ubuntu 22.04 运行库、Python 启动器和输入验证；**没有 SRBMiner 二进制**。
- 首次运行下载固定原始归档，完整保留作者 `ReadMe.txt` 与随包许可/脚本，不修改二进制、不运行附带脚本。
- 默认 SRBMiner `pearlhash` 开发费 **2%**，Kryptex 矿池费 **3%**；两者独立，不是本项目收费，也不应简单当作精确总扣费比例。变更矿池前核对其费用与 TLS 端口。
- 只挖 Pearl，禁用 CPU、MSR/大页调整、AMD/Intel、GPU 超频及 autotune 配置加载；不开放 API、不带其他人的钱包/推荐码。

## 安全边界与缓存

闭源矿工仍是第三方可执行代码：固定校验只能锁定下载内容，**不能证明软件安全**。不要把 NAS 数据、宿主根目录、Docker socket、密钥或钱包文件挂入容器；建议独立机器/隔离网络。

Compose 使用 UID/GID 10001、只读根目录、drop ALL capabilities、no-new-privileges、普通 `init: true`、指定单张 GPU、无端口、无 privileged/host network。`restart: "no"` 避免失败后不断重试。

- `miner-cache` 是项目专用 Docker named volume，Docker 首次创建时继承镜像目录 UID 10001。不要改成已有 NAS bind mount，也不要与不可信容器共用。
- 缓存仅保存校验过的原始归档；**每次启动重新验证 SHA256**，然后在私有 `/run/pearl` 可执行 tmpfs 中重新解包，拒绝路径穿越、软/硬链接、特殊文件、重复路径和超限内容。运行目录是原始 release 目录，支持上游相对路径行为。
- `/tmp` 是独立 noexec tmpfs；`/run/pearl` 必须允许执行，否则无法启动。停止容器后 tmpfs 消失。
- 校验错误不会自动替换缓存，更不会继续执行。先停止该项目，确认问题后可在**仅含本服务的新配置目录**执行 `docker compose down -v` 删除该项目专用缓存，再重试；不要删除其他 Docker/NAS 数据。
- 不删除 `/.dockerenv`、不隐藏容器、不绕过上游授权或修改专有程序。如原版拒绝运行，保留日志并停止，不承诺 `init` 能修复上游兼容问题。

## 固定版本与验证

原始下载：[作者 SRBMiner 3.8.0 Linux](https://github.com/doktor83/SRBMiner-Multi/releases/download/3.8.0/SRBMiner-Multi-3-8-0-Linux.tar.gz)

```
SHA256 095c3f75905ee023e8ed85ac905afefc92825cce83a528fa955cf1db456d3dd8
MD5    01cdd7ffdca43f3b6968fbaacea449b5
```

SHA256 是 2026-10-26 下载原作者归档后本地计算的固定值，不冒称作者签名/发布的 SHA256；MD5 与作者发布页一致。运行时使用强 SHA256，不允许环境变量覆盖版本、下载 URL 或 hash。升级需要审阅后改代码并发布新标签。

`tests/test_recipe.py` 只生成并执行我们自己的打印参数 mock，验证输入、默认 TLS 端口、归档校验/缓存/解包；从不执行真正矿工（也不执行其 help/version）。CI 手动触发构建，可选择发布 GHCR；容器 smoke 使用 `--network none` 且缺少钱包，必须在下载前失败。详见 [验证范围](VALIDATION.md) 和 [来源](SOURCES.md)。

旧的手工挂载矿工与 `Dockerfile.private` 流程已经退役，避免用户额外构建/下载。目标是 pull 后配置自己的两项信息即可启动，不代表当前候选镜像已上架或已经验证出币。
