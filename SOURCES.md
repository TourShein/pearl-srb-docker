# 一手来源（查阅：2026-10-29）

- [SRBMiner 3.8.1 发布](https://github.com/doktor83/SRBMiner-Multi/releases/tag/3.8.1)：版本、归档 MD5、NVIDIA Pearl 更新。
- [3.8.1 参数](https://github.com/doktor83/SRBMiner-Multi/blob/3.8.1/Parameters)：algorithm、disable-cpu、tls、gpu-disable-oc、autotune-no-load。
- [作者 README 与许可](https://github.com/doktor83/SRBMiner-Multi/blob/3.8.1/README.md)：闭源二进制限制及算法费用。README 列 pearlhash 开发费为 2%；不是本配方另加费用。
- [Docker GPU reservation](https://docs.docker.com/compose/how-tos/gpu-support/)：device_ids 和 capabilities。
- [NVIDIA 容器能力与 UUID](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html)：compute,utility 与设备限制。
- [Kryptex Pearl 设置](https://pool.kryptex.com/prl)、[矿池自己的 SRB 指南](https://pool.kryptex.com/en/articles/how-to-mine-pearl-en)：矿池端口须现场确认，SRB TLS 开关。

发布页签名提交不等同于下载二进制已被签名或审计；不作安全背书。

## 本地固定值来源
2026-10-29 从作者 3.8.1 Linux 发布下载地址取得原始归档：MD5 与发布页一致，计算 SHA256 为 `2f65b3b7f7781def46610c43b8a10a3d38033f6cf4ef6cc968b405ca9b0ce807`。此值也匹配 GitHub release asset 的 SHA256 digest，但不等于作者签名或安全审计。默认 Kryptex 端点为 `prl.kryptex.network:8048`（TLS），矿池费 3%；SRBMiner pearlhash 开发费 2%。

## 分发边界
已检查 3.8.1 官方 README 的 LICENSE 与 Linux 包内 ReadMe.txt。官方 README 对专有 GPU 二进制的再分发/发布/并入其他产品要求事先书面许可；包内仅有第三方组件条款，没有额外授予本项目再分发 SRBMiner 的权利。公开镜像不含矿工，仅让获授权使用硬件的用户从原作者下载未修改官方发布包；不能把这理解为整体再分发许可。

