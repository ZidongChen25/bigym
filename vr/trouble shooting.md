# WiVRn Hard-Lock Troubleshooting Note

## 简体中文

### 为什么现在可以推断 `pcie_aspm=off usbcore.autosuspend=-1` 绕过了整机锁死

这不是对根因的严格证明，但当前证据链已经足够强，可以支持这个判断。

判断依据如下：

1. 修改前，问题表现为运行一段时间后整机锁死，而不是应用一启动就退出。
2. 问题在绕过 WiVRn dashboard、直接运行 `wivrn-server` 时仍然出现，所以它不是单纯的 dashboard / ADB 前端问题。
3. 这台机器使用的是 ASUS B650 系列主板，这与已有的 WiVRn 相关整机锁死案例非常接近；这些案例最后通常通过关闭 PCIe ASPM 和 USB autosuspend 获得稳定。
4. 修改后，内核启动参数已经确认生效，可以从 `cat /proc/cmdline` 中看到：

```bash
pcie_aspm=off usbcore.autosuspend=-1
```

5. 在相似的 VR 负载下，整机锁死这一级问题没有再次出现。

基于以上事实，更合理的解释是：

- WiVRn 或 VR 负载本身更像是触发条件，而不是唯一根因。
- 真正导致整机锁死的，更可能是 PCIe 省电、USB 省电、主板固件、内核和驱动之间的交互问题。
- `pcie_aspm=off usbcore.autosuspend=-1` 关闭了最可疑的两条省电路径，因此绕过了导致整机锁死的那一层问题。

### 这不代表什么

这不代表所有问题都已经彻底修复。

如果后续仍然出现以下现象：

- BiGym 画面闪退
- VR viewer 消失
- demo recorder GUI 仍然显示进程未退出

那么这些更像是应用层、OpenXR、渲染链路或进程生命周期管理的问题，而不是之前的整机锁死问题。

换句话说：

- 整机锁死问题，很可能已经被当前内核参数绕过。
- 应用层闪退或 viewer 异常退出，仍然需要单独排查。

### 如何再次验证

先确认参数仍然生效：

```bash
cat /proc/cmdline
```

如果以后又发生整机锁死，重启后优先查看上一轮开机的内核日志：

```bash
sudo journalctl -o short-precise -k -b -1 | tail -n 100
```

### 当前结论

当前更合理的结论不是“WiVRn 本身已经完全修好”，而是：

> 之前那种运行一段时间后整机锁死的问题，大概率已经被 `pcie_aspm=off usbcore.autosuspend=-1` 绕过；后续剩余的问题应视为独立的应用层或渲染层问题。

## English

### Why it is now reasonable to conclude that `pcie_aspm=off usbcore.autosuspend=-1` worked around the full-system hard lock

This is not a strict proof of root cause, but the current evidence is strong enough to support that conclusion.

The reasoning is:

1. Before the change, the failure mode was a full-system hard lock after some runtime, not an immediate application exit.
2. The hard lock still reproduced when bypassing the WiVRn dashboard and running `wivrn-server` directly, so it was not just a dashboard / ADB frontend problem.
3. The machine uses an ASUS B650-family motherboard, which matches previously reported WiVRn-related hard-lock patterns where stability improved after disabling PCIe ASPM and USB autosuspend.
4. After the change, the kernel command line was confirmed to contain:

```bash
pcie_aspm=off usbcore.autosuspend=-1
```

5. Under similar VR workload, the full-system hard lock no longer reappeared.

Given those observations, the more plausible explanation is:

- WiVRn or the VR workload was acting as the trigger, not necessarily the sole root cause.
- The actual hard-lock path was more likely related to PCIe power saving, USB power saving, motherboard firmware, kernel behavior, or driver interaction.
- Disabling PCIe ASPM and USB autosuspend removed the two most suspicious power-management paths, which likely bypassed the layer causing the full-system freeze.

### What this does not mean

This does not mean that every remaining issue is fixed.

If later failures still look like:

- the BiGym window disappearing
- the VR viewer exiting or becoming invisible
- the demo recorder GUI still thinking the process is alive until `Stop` is pressed

then those should be treated as application-level, OpenXR-level, rendering-path, or process-lifecycle issues, not as the same full-system hard-lock problem.

In other words:

- the hard-lock layer is likely bypassed now
- application-level crashes or viewer exits still need separate debugging

### How to verify again

First confirm the kernel parameters are still active:

```bash
cat /proc/cmdline
```

If a full-system lock ever happens again, check the previous boot's kernel log after reboot:

```bash
sudo journalctl -o short-precise -k -b -1 | tail -n 100
```

### Current conclusion

The more accurate conclusion is not “WiVRn is fully fixed”, but:

> The previous full-system hard-lock that happened after some runtime was very likely worked around by `pcie_aspm=off usbcore.autosuspend=-1`; any remaining issues should be treated as separate application-level or rendering-level problems.
