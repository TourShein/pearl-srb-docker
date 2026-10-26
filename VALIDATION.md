# 验证报告 — 2026-10-26

## 已通过

- `sh -n entrypoint.sh`：shell 语法通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_recipe.py`：4 组测试通过。
- 测试包括合成 PRL Bech32m 公钥地址、26 项无效输入、固定算法/TLS/CPU 关闭等 argv、拒绝额外命令参数、错误钱包/UUID 时不执行 mock，以及 Compose 静态安全断言。
- mock 是测试临时创建的 `printf` 脚本，不是真矿工；没有执行任何下载程序。
- 人工核对上游 3.8.0 参数、归档 MD5、Docker GPU reservation 和 NVIDIA UUID/capability 文档。

## 未运行 / 未验证

没有下载矿工，没有实际归档 SHA256，没有 Docker build / Compose config 解析，没有 NVIDIA GPU 或矿池连接测试，没有份额/性能/功耗/温度数据。Dockerfile 的版本、路径、基础镜像、系统库兼容性与只读运行均仍需目标主机验证。静态断言不是 Docker schema 校验，mock 通过也不等于矿工能运行。

没有安装软件、修改系统设置、修改功率/频率、发布仓库或镜像。用户后来提出云端仓库与镜像发布，属于后续待明确的发布流程；此文件不声称该流程已完成。

## 发布门槛

当前主 Dockerfile 已改为不含矿工的 runtime-only 镜像；Compose 只读挂载用户自行准备的官方发布目录。Dockerfile.private 保留私有构建路线，不得推送其产物。已添加人工触发 GHCR workflow，但没有创建仓库、运行 CI 或推送镜像。构建/推送不等于获准在 CI 或云端挖矿。

更新：runtime-only 改造后重新运行 shell 语法及全部 4 组测试，通过。用现有 PyYAML 对 compose.yaml 和 workflow 做了基础 YAML 解析，通过；这不是 Docker/GitHub 的完整语义校验。主镜像静态检查无 vendor COPY，Compose 的唯一 bind 为 /opt/srb 只读且禁止自动创建缺失源目录。
