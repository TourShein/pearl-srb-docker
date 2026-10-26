# 社区证据怎么读

- [独立部署者的公开测试记录](https://github.com/pvandenburg1234-eng/pearl-salad-nvidia/blob/main/BENCHMARKS.md)包含多种 NVIDIA/AMD 卡及 SRB、BzMiner、KRig 的比较。它把短测定义为 300 秒，并用矿工报告算力扣开发费计算 effective 值；这不是实收币、盈利或安全审计。单主机结果不能代表所有显卡、矿池或 SRB 3.8.0。
- “有人在容器中成功提交份额”只说明那套特定版本/驱动/硬件组合曾工作，不证明现在这个配方已经跑通。PID 1 init 也不是所有兼容问题的通用解法。
- 本包选择重写最小专用 wrapper，而非继承旧通用镜像的 CPU 默认、其他币种钱包、推荐码、容器标识删除或超频配置。
- 闭源软件无法仅凭 GitHub 星数、杀毒结果、短测算力获得可信安全保证。实际选择应看目标 GPU 同版本对照、长期 accepted/rejected shares、矿池统计与总电耗；本包没有代做这些实测。
