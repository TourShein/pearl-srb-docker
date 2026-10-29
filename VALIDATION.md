# 3.8.1 更新验证（2026-10-29）

- 独立下载原作者 Linux 归档，未运行矿工。SHA256 `2f65b3b7f7781def46610c43b8a10a3d38033f6cf4ef6cc968b405ca9b0ce807` 与 GitHub asset digest 一致；MD5 `f7d94347dfae5e629225a3c14bc12794` 与发布页一致。
- 官方归档 7 个条目，保留全部官方文件与 ReadMe；没有将二进制或归档纳入仓库/镜像。
- 检查官方许可：未取得公开预装再分发授权，因此维持用户运行时从作者下载官方包的 bootstrap 方式。
- 11 项离线单元测试与 shell 语法检查通过。测试覆盖版本固定、禁止环境覆盖、保留 3.8.0 缓存、3.8.1 独立缓存与新 power tuner 不启用；测试只执行自写 mock，不执行真实矿工。
- 3.8.1 Docker 构建、容器 smoke、GHCR 发布与匿名读取需等待本次 CI。当前执行环境无 Docker，不能声称本地容器验证通过。
- 不更改用户 Unraid、GPU、钱包或安全设置；不运行挖矿，不验证真实 GPU 算力/份额。
- 发布工作流只推送 `bootstrap-3.8.1` 与本次 `sha-*` 标签，不推送 `bootstrap-3.8.0` 或 `latest`。

---

# 验证记录（2026-10-26）

## 已完成
- 原作者 3.8.0 Linux 归档只下载/静态检查，未执行。MD5 与发布页一致；SHA256 固定在 bootstrap.py/README。
- 静态归档：唯一顶层 SRBMiner-Multi-3-8-0，7 个条目，无软/硬链接、动态库或路径穿越；ReadMe.txt 包含许可。完整保留。
- readelf 静态检查（未用 ldd、未执行二进制）：NEEDED 为 glibc/pthread/dl/rt/m/动态加载器；没有 RPATH/RUNPATH。GPU 驱动动态加载仍需实机验证。
- 8 项本地离线单元测试通过，包括仅运行自写 shell mock 的启动参数测试；非法钱包/UUID、设备不匹配、下载 hash 错误、损坏缓存、默认 8048 TLS、穿越与 symlink 均覆盖。缓存重用不重复下载，每次从已验证归档新解包而不是信任旧可执行文件。
- shell 语法检查通过；无真实挖矿、无矿池连接、无任何真实钱包。

## 尚未验证
- 本执行环境没有 docker 命令，故不能本地构建/运行容器；CI 内提供构建与无网络、无钱包的容器 smoke，须查看最终 commit 的 CI 结果。
- GHCR 包发布、Public 可见性、匿名 pull 均需发布后验证；本记录不表示镜像已经存在。
- 没有真实 NVIDIA GPU / Unraid 运行、驱动兼容性、矿池 accepted shares、算力、收益或长期稳定性验证。
- 固定 hash、容器隔离及社区测试不等于闭源程序的安全审计或担保。

## 发布后验证（2026-10-26 05:32 UTC）

- GitHub Actions run `40274295899` 成功，构建源码 `ecabc0d13453f5ac5dfa9533a8f2b081a1e339b9`，job 3m06s。包括 8 项 mock 测试、Docker build、无网络且缺钱包的容器 smoke，以及 GHCR push。
- 仓库与镜像包均已在 GitHub UI 确认为 Public。
- 不带用户凭据，通过 GHCR 标准匿名 pull token 获取 manifest 与 config，均 HTTP 200；清单 digest 与本地计算匹配：`sha256:d7118c3768b4bb884133b4d7ba612e3d8a70b45cfcce14950de24e2187eec855`。平台 linux/amd64，容器用户 10001:10001。
- 未在本地执行完整 docker pull；未下载运行镜像中的真实矿工，未做 GPU/Unraid 实测。矿工归档只用于静态检查，没有执行。

