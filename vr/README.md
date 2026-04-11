# VR Setup and Demo Collection

This README documents a WiVRn-based VR workflow for BiGym on Ubuntu.

The VR code in this workspace is aligned with upstream `Nagi-ovo/bigym`, but the setup instructions below intentionally use `WiVRn` for Quest-on-Ubuntu instead of the older SteamVR-first workflow.

GitHub Markdown does not support true tabs without JavaScript, so this file uses `<details>` blocks for one-click language switching.

<details open>
<summary><strong>English</strong></summary>

## Overview

For BiGym on Ubuntu with a Meta Quest headset, use this flow:

1. Install and start `WiVRn` on the Ubuntu host.
2. Connect the Quest headset to the host through the WiVRn client.
3. Launch BiGym from your existing Python environment.
4. Use the demo recorder to collect VR demonstrations.

BiGym's VR viewer is an OpenXR application built on `pyopenxr`, so WiVRn is the relevant runtime path for Quest on Ubuntu.

## Host Requirements

Before you start, make sure:

- the Ubuntu host can already run BiGym normally
- the host and the Quest headset are on the same network
- `avahi-daemon` is installed and running
- if a firewall is enabled, `5353/udp` and `9757/tcp+udp` are open

Recommended host packages:

```bash
sudo apt update
sudo apt install -y flatpak avahi-daemon adb pavucontrol
```

Enable Avahi:

```bash
sudo systemctl enable --now avahi-daemon
```

If you use UFW:

```bash
sudo ufw allow 5353/udp
sudo ufw allow 9757
```

## Install WiVRn

Add Flathub if needed:

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

Install WiVRn:

```bash
flatpak install flathub io.github.wivrn.wivrn
```

Start the WiVRn dashboard:

```bash
flatpak run io.github.wivrn.wivrn
```

Then follow the WiVRn pairing wizard on the host and on the Quest headset.

## Connect Quest To The Host

Once WiVRn is installed on both sides:

1. Start the WiVRn dashboard on the Ubuntu host.
2. Start the WiVRn client on the Quest headset.
3. Select the Ubuntu host from the headset and connect.
4. Wait until WiVRn shows that the connection is ready.

If auto-discovery does not work:

- confirm both devices are on the same network
- confirm `avahi-daemon` is running
- confirm `5353/udp` is not blocked
- confirm `9757/tcp` and `9757/udp` are not blocked

## Launch BiGym

Run BiGym natively on the Ubuntu host from your existing environment:

```bash
cd /home/${USER}/bigym
conda activate <your_bigym_env>
pip install -e ".[dev]"
python tools/demo_recorder/main.py
```

Important order:

1. connect the headset through WiVRn first
2. then run `python tools/demo_recorder/main.py`

## Recorder GUI

In the recorder window:

- `Environment`: choose the task
- `Robot Model`: usually `Default`
- `Control Profile`: choose the profile matching the robot
- `Output Directory`: choose a task-specific directory
- `Record`: launches the VR viewer

Recommended convention:

- one task per output directory
- example: `/home/${USER}/bigym/vr_demos/MovePlate`

## Move Plate Example

Recommended settings for `Move Plate`:

- `Environment = Move Plate`
- `Robot Model = Default`
- `Control Profile = H1 Upper Body Floating`
- `Floating Base DOFs = X, Y, RZ`

The `Z` floating DOF is usually not needed for this task.

## Quest Controller Mapping

The current VR input code includes Meta Quest Touch bindings.

### Demo Recording Controls

- left `X`: start a new recording
- left `Y`: save the current recording
- right thumbstick up/down: adjust vertical world offset

### H1 Upper Body Floating Controls

- move left controller: control the left arm target
- move right controller: control the right arm target
- move and rotate the headset: control the floating base
- left trigger: control the left gripper
- right trigger: control the right gripper
- right `A`: toggle position synchronization
- right `B`: toggle rotation synchronization

## Move Plate Collection Procedure

To collect one `Move Plate` demonstration:

1. Start WiVRn on the Ubuntu host.
2. Connect the Quest headset.
3. Run `python tools/demo_recorder/main.py`.
4. In the GUI, choose:
   - `Environment = Move Plate`
   - `Robot Model = Default`
   - `Control Profile = H1 Upper Body Floating`
   - `Floating Base DOFs = X, Y, RZ`
   - `Output Directory = /home/${USER}/bigym/vr_demos/MovePlate`
5. Click `Record`.
6. Put on the headset and wait for the scene to stabilize.
7. Press left `X` to start a fresh recording.
8. Move to the source rack, grasp the plate, lift it clear of the rack and table, and move it to the target rack.
9. Place the plate upright into the target rack.
10. Release the gripper.
11. After success, press left `Y` to save the demo.

Notes:

- pressing left `X` resets the environment and starts a new attempt
- successful completion stops recording after a short countdown
- success does not save automatically; you still need left `Y`

## Saved Files And Validation

Recorded demos are saved as `.safetensors` files in the selected output directory.

To replay them locally:

```bash
python tools/demo_player/main.py
```

Then point the player to your saved demo directory and replay one or more files.

## Audio Notes

When the headset is connected, WiVRn creates virtual audio devices.

If audio is missing:

- select the `WiVRn` output device in your desktop sound settings or `pavucontrol`
- if you need microphone input, enable the headset microphone and select `WiVRn(microphone)` on the host

## References

- WiVRn homepage: https://wivrn.github.io/
- WiVRn GitHub: https://github.com/WiVRn/WiVRn
- Flathub installation docs: https://docs.flathub.org/docs/for-users/installation

</details>

<details>
<summary><strong>中文</strong></summary>

## 概览

这个 README 说明如何在 Ubuntu 上通过 `WiVRn` 使用 Meta Quest 为 BiGym 采集 VR 数据。

这个工作区里的 VR 代码已经和上游 `Nagi-ovo/bigym` 对齐，但这里的文档主流程仍然是 `WiVRn`，不是旧的 SteamVR-first 路线。

推荐流程是：

1. 在 Ubuntu 宿主机安装并启动 `WiVRn`
2. 用 Quest 头显上的 WiVRn 客户端连接宿主机
3. 用你现有的 Python 环境原生启动 BiGym
4. 通过 demo recorder 采集 VR 演示数据

BiGym 的 VR viewer 本身就是基于 `pyopenxr` 的 OpenXR 应用，所以对 Quest + Ubuntu 来说，WiVRn 是相关的运行路径。

## 宿主机要求

开始之前，请确认：

- Ubuntu 宿主机已经能正常运行 BiGym
- 宿主机和 Quest 头显在同一个网络
- `avahi-daemon` 已安装并运行
- 如果启用了防火墙，已经放行 `5353/udp` 和 `9757/tcp+udp`

建议先安装这些宿主机组件：

```bash
sudo apt update
sudo apt install -y flatpak avahi-daemon adb pavucontrol
```

启动并设为开机运行 Avahi：

```bash
sudo systemctl enable --now avahi-daemon
```

如果你使用 UFW：

```bash
sudo ufw allow 5353/udp
sudo ufw allow 9757
```

## 安装 WiVRn

如果还没有 Flathub，先添加：

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

安装 WiVRn：

```bash
flatpak install flathub io.github.wivrn.wivrn
```

启动 WiVRn dashboard：

```bash
flatpak run io.github.wivrn.wivrn
```

然后按照宿主机和 Quest 头显上的 WiVRn 向导完成配对。

## 连接 Quest 和宿主机

当 WiVRn 两边都装好以后：

1. 在 Ubuntu 宿主机启动 WiVRn dashboard
2. 在 Quest 头显中启动 WiVRn 客户端
3. 在头显中选择 Ubuntu 宿主机并连接
4. 等待 WiVRn 显示连接就绪

如果自动发现失败：

- 确认两台设备在同一个网络
- 确认 `avahi-daemon` 正在运行
- 确认 `5353/udp` 没被防火墙拦住
- 确认 `9757/tcp` 和 `9757/udp` 没被防火墙拦住

## 启动 BiGym

在 Ubuntu 宿主机上用你现有的环境原生启动：

```bash
cd /home/${USER}/bigym
conda activate <你的_bigym_env>
pip install -e ".[dev]"
python tools/demo_recorder/main.py
```

顺序很重要：

1. 先通过 WiVRn 连上头显
2. 再运行 `python tools/demo_recorder/main.py`

## Recorder 图形界面

在 recorder 窗口中：

- `Environment`：选择任务
- `Robot Model`：通常选 `Default`
- `Control Profile`：选择和机器人匹配的控制配置
- `Output Directory`：选择当前任务专用的输出目录
- `Record`：启动 VR viewer

建议约定：

- 一个任务对应一个输出目录
- 例如：`/home/${USER}/bigym/vr_demos/MovePlate`

## Move Plate 示例配置

录制 `Move Plate` 时，建议：

- `Environment = Move Plate`
- `Robot Model = Default`
- `Control Profile = H1 Upper Body Floating`
- `Floating Base DOFs = X, Y, RZ`

通常不需要打开 `Z` 这个浮动自由度。

## Quest 手柄映射

当前 VR 输入代码已经包含 Meta Quest Touch 的 binding。

### Demo 录制控制

- 左手 `X`：开始新的录制
- 左手 `Y`：保存当前录制
- 右手摇杆上下：调节世界坐标系的竖直偏移

### H1 Upper Body Floating 控制

- 移动左手柄：控制左臂目标
- 移动右手柄：控制右臂目标
- 移动和转动头显：控制浮动底座
- 左 trigger：控制左夹爪
- 右 trigger：控制右夹爪
- 右手 `A`：切换位置同步
- 右手 `B`：切换旋转同步

## Move Plate 采集步骤

如果你要采一条 `Move Plate` demo，按下面操作：

1. 在 Ubuntu 宿主机启动 WiVRn
2. 连接 Quest 头显
3. 运行 `python tools/demo_recorder/main.py`
4. 在 GUI 中选择：
   - `Environment = Move Plate`
   - `Robot Model = Default`
   - `Control Profile = H1 Upper Body Floating`
   - `Floating Base DOFs = X, Y, RZ`
   - `Output Directory = /home/${USER}/bigym/vr_demos/MovePlate`
5. 点击 `Record`
6. 戴上头显，等待场景稳定
7. 按左手 `X` 开始一条新录制
8. 走到起始 rack，抓住 plate，把它提离 rack 和桌面，再移动到目标 rack
9. 把 plate 竖直放进目标 rack
10. 松开夹爪
11. 成功后按左手 `Y` 保存 demo

补充说明：

- 按左手 `X` 会重置环境并开始新尝试
- 成功后系统会在短暂倒计时后停止录制
- 但不会自动保存，仍然要按左手 `Y`

## 保存结果和回放

录制结果会以 `.safetensors` 文件保存到你选择的输出目录。

本地回放验证：

```bash
python tools/demo_player/main.py
```

然后把播放器指向你的 demo 目录，选择一个或多个文件进行回放。

## 音频说明

头显连上以后，WiVRn 会创建虚拟音频设备。

如果没有声音：

- 在系统声音设置或 `pavucontrol` 中把 `WiVRn` 设成输出设备
- 如果你需要麦克风，在头显里开启麦克风，然后在宿主机上选择 `WiVRn(microphone)`

## 参考链接

- WiVRn 主页: https://wivrn.github.io/
- WiVRn GitHub: https://github.com/WiVRn/WiVRn
- Flathub 安装文档: https://docs.flathub.org/docs/for-users/installation

</details>
  sudo journalctl -k -b -1 --no-pager | rg -n "NVRM|Xid|nvidia|drm|watchdog|panic|BUG:|lockup|gpu"