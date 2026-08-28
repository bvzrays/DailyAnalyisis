# DailyAnalyisis

<p align="center">
  <a href="https://github.com/bvzrays/DailyAnalyisis"><img src="./ICON.png" width="256" height="256" alt="DailyAnalyisis"></a>
</p>
<h1 align="center">DailyAnalyisis 5.0.9</h1>
<h4 align="center">✨ 面向 GsCore / 早柚核心的群聊分析、可视化日报与每日群漫画插件 ✨</h4>
<div align="center">
  <a href="https://docs.sayu-bot.com/" target="_blank">GsCore 文档</a> &nbsp; · &nbsp;
  <a href="https://docs.sayu-bot.com/CodePlugins" target="_blank">插件开发指南</a> &nbsp; · &nbsp;
  <a href="https://github.com/SXP-Simon/astrbot_plugin_qq_group_daily_analysis" target="_blank">原始项目</a>
</div>

## 丨安装提醒

> [!IMPORTANT]
> 本插件是 [GsCore / 早柚核心](https://github.com/Genshin-bots/gsuid_core) 插件，不是 AstrBot 插件。分析、定时任务、消息存档、WebUI 与 AI 调用均在 GsCore 进程内完成。
>
> 使用 `astrbot_plugin_gscore_adapter` 时，AstrBot 仅作为 GsCore 的消息平台适配器；插件不依赖 AstrBot 的插件系统、配置中心或 LLM Provider。换用其他 GsCore 适配器时无需修改插件。

## 丨安装方式

### WebConsole 安装

1. 打开 GsCore WebConsole 的插件商店。
2. 选择“通过 URL 安装”并填写：

   ```text
   https://github.com/bvzrays/DailyAnalyisis
   ```

3. 确认核心配置中的“自动安装插件依赖”已开启。
4. 安装完成后重载插件或重启 GsCore。

### 手动安装

在 GsCore 仓库根目录执行：

```sh
cd gsuid_core/plugins
   git clone https://github.com/bvzrays/DailyAnalyisis.git DailyAnalyisis
cd ../..
uv run core
```

若 GsCore 正在运行，可先停止进程，再执行最后一条启动命令。

## 丨功能

<details><summary><b>群聊智能分析</b></summary><p>

- 按指定天数读取群聊记录，生成基础统计、24 小时活跃度、话题、群友称号、MBTI、金句与聊天质量评价。
- 支持图片、文本、HTML 单独输出或组合输出。
- 支持群白名单、黑名单、机器人消息过滤、最小消息数和最大消息数限制。

</p></details>

<details><summary><b>可视化报告与主题</b></summary><p>

- 完整保留上游内置报告模板与静态资源。
- 支持两轮 HTML 转图片渲染、字体源切换、视口与质量参数调整。
- 支持 HTML 报告落盘、自建公开地址和仅发送 URL。

</p></details>

<details><summary><b>每日群漫画</b></summary><p>

- 可从群聊话题独立生成漫画，也可在群分析完成后自动联动。
- 支持角色方案、参考图、多个绘图 Provider、失败回退、代理、重试与并发控制。
- 支持将漫画额外上传至兼容平台的群相册。
- 漫画分镜可使用普通文本模型，但最终出图必须配置真正支持图片生成的模型。

</p></details>

<details><summary><b>定时与增量分析</b></summary><p>

- 支持每日定时分析、独立目标群列表和传统完整报告。
- 支持按消息数量分批的增量分析、滑动窗口汇总、即时报告调试模式与传统分析回退。
- 主动任务复用 GsCore 调度器，插件关闭时会正确释放任务和资源。

</p></details>

<details><summary><b>跨平台消息存档</b></summary><p>

- 将 GsCore 抽象消息持久化到插件独立 SQLite 数据库，不受核心短期内存历史长度限制。
- 统一记录文本、图片、回复、发送者与群聊信息，供手动、定时和增量分析共同使用。
- 平台能力由当前 GsCore 适配器决定；基础分析不绑定 OneBot 或 AstrBot。

</p></details>

<details><summary><b>专用 WebUI</b></summary><p>

- 提供运行总览、活跃任务、分析记录、统计消耗、历史报告、日志和完整配置中心。
- 配置页面直接读取最新版 `_conf_schema.json`，12 个配置组、101 个叶子配置全部可编辑。
- WebUI 与 26 个插件 API 直接挂载到 GsCore 的 FastAPI 应用。
- WebUI 首次访问必须设置独立密码，业务 API 全部受密码会话保护。

</p></details>

## 丨效果

### 1. 群分析报告

下列为不同报告主题的实际渲染效果，点击图片可查看原图。

<table>
  <tr>
    <td><a href="./DailyAnalyisis/assets/scrapbook-demo.jpg"><img src="./DailyAnalyisis/assets/scrapbook-demo.jpg" height="520" alt="scrapbook 主题"></a></td>
    <td><a href="./DailyAnalyisis/assets/retro_futurism-demo.jpg"><img src="./DailyAnalyisis/assets/retro_futurism-demo.jpg" height="520" alt="retro futurism 主题"></a></td>
    <td><a href="./DailyAnalyisis/assets/HatsuneMiku-demo.jpg"><img src="./DailyAnalyisis/assets/HatsuneMiku-demo.jpg" height="520" alt="Hatsune Miku 主题"></a></td>
  </tr>
  <tr>
    <td><a href="./DailyAnalyisis/assets/hack-demo.jpg"><img src="./DailyAnalyisis/assets/hack-demo.jpg" height="520" alt="hack 主题"></a></td>
    <td><a href="./DailyAnalyisis/assets/ATRI-demo.jpg"><img src="./DailyAnalyisis/assets/ATRI-demo.jpg" height="520" alt="ATRI 主题"></a></td>
    <td><a href="./DailyAnalyisis/assets/BlueArchive-demo.jpg"><img src="./DailyAnalyisis/assets/BlueArchive-demo.jpg" height="520" alt="Blue Archive 主题"></a></td>
  </tr>
  <tr>
    <td><a href="./DailyAnalyisis/assets/simple-demo.jpg"><img src="./DailyAnalyisis/assets/simple-demo.jpg" height="520" alt="simple 主题"></a></td>
    <td><a href="./DailyAnalyisis/assets/spring_festival-demo.jpg"><img src="./DailyAnalyisis/assets/spring_festival-demo.jpg" height="520" alt="春节主题"></a></td>
    <td><a href="./DailyAnalyisis/assets/comic-demo.jpg"><img src="./DailyAnalyisis/assets/comic-demo.jpg" height="520" alt="每日群漫画"></a></td>
  </tr>
</table>

### 2. 报告格式

插件支持图片、文本、HTML 以及组合输出；HTML 报告也可以保存到本地或通过公开地址访问。

<p align="center">
  <a href="./DailyAnalyisis/assets/format-demo.jpg"><img src="./DailyAnalyisis/assets/format-demo.jpg" height="520" alt="报告格式示例"></a>
</p>

## 丨指令

以下指令与上游 5.0.8 一一对应，均需在群聊中由管理员使用。本插件固定使用 `day` 作为指令前缀。

| 指令 | 英文别名 | 说明 |
|---|---|---|
| `day群分析 [天数]` | `group_analysis` | 生成最近指定天数的群聊分析报告；不填时使用配置默认值 |
| `day群漫画 [天数]` | `group_comic`、`daily_comic` | 独立提取话题并生成群漫画，不额外生成日报 |
| `day设置格式 [格式]` | `set_format` | 查看或设置 `image`、`text`、`html`，支持逗号组合 |
| `day设置模板 [名称/序号/随机]` | `set_template` | 查看当前模板或切换报告模板；新安装默认 ATRI，可设置为随机 |
| `day查看模板` | `view_templates` | 查看全部报告模板及预览 |
| `day分析设置 [动作]` | `analysis_settings` | 管理当前群分析状态与调试开关 |
| `day增量状态` | `incremental_status` | 查看当前滑动窗口内的增量分析状态 |
| `day概览` | `overview` | 以图片查看运行总览、统计、Token/成本消耗和当前任务 |

`day分析设置` 支持以下动作：

| 动作 | 说明 |
|---|---|
| `enable` / `disable` | 启用或禁用当前群 |
| `status` | 查看当前群、定时、增量、输出格式等状态 |
| `reload` | 重新加载定时任务与增量目标状态 |
| `test` | 立即测试一次自动分析和报告投递 |
| `filter_bot` | 切换是否过滤机器人自身消息 |
| `incremental_debug` | 切换增量分析立即报告模式 |

## 丨配置

插件完整保留上游 `_conf_schema.json`，并将全部配置项同步映射到 GsCore 配置中心。LLM 的 API Key、端点、模型、温度、输出上限和超时均属于本插件配置；复杂角色方案和绘图后端表在 GsCore 配置中心以 JSON 编辑，在插件专用 WebUI 中则使用结构化表单编辑。

| 配置组 | 主要内容 |
|---|---|
| GsCore 总览 | 插件总开关、外部 WebUI 开关（默认关闭） |
| 基础设置 | 群名单、分析天数、消息阈值、输出格式、模板（新安装默认 ATRI/随机）、用户卡片和调试开关 |
| WebUI 安全 | 首次访问密码、会话保护和公网访问安全设置 |
| QQ 官方机器人 | QQ 官方 Markdown 报告概览图 |
| 图片渲染策略 | 两轮渲染格式、质量、缩放、超时、视口和字体源 |
| 定时分析设置 | 定时时间、目标群名单与继承模式 |
| LLM 设置 | 插件专用 API Key、端点、模型、温度、输出上限、超时、重试、退避和流式调用 |
| 分析功能 | 话题、称号、金句、质量评价、数量上限与人格策略 |
| 每日群漫画 | 漫画开关、目标群、角色、参考图、绘图后端、Provider 和重试 |
| 增量分析 | 目标群、批次阈值、即时报告和传统分析回退 |
| HTML 报告 | 输出目录、公开基址、文件名格式和仅 URL 模式 |
| 群文件与相册 | 报告文件、报告相册和漫画相册上传 |
| 提示词 | 话题、称号、金句、质量评价和漫画分镜提示词 |
| 性能设置 | 群任务、LLM、渲染并发和多群错峰间隔 |

完整配置入口：

- GsCore WebConsole：插件配置 → `DailyAnalyisis`
- 插件 WebUI：`http://127.0.0.1:8765/daily-analyisis-gscore/`
- 本地数据：`data/DailyAnalyisis/config.json`

WebConsole 参数区按“总览、基础配置、展示配置”拆分为 3 个原生配置标签；其中基础配置和展示配置内部仍按功能分隔，并保留全部 schema 字段。插件 WebUI 同样按两栏导航展示，不需要在单一长表单中查找。配置保存时，插件专用配置与 GsCore 配置会自动同步；从 GsCore 配置中心修改后建议重载插件。

外部 WebUI 默认关闭。需要使用时，先在 GsCore WebConsole 的 `群分析·总览 → 启用外部 WebUI` 中开启；开启后第一次进入页面会要求设置独立访问密码。密码只以 PBKDF2-SHA256 摘要保存，不会写入明文。之后可在 `DailyAnalyisis基础配置 → 群分析·WebUI安全 → WebUI访问密码` 中输入新密码，保存后立即生效并使旧会话失效。公网部署还应使用 HTTPS 和反向代理，不要直接暴露未加密的 HTTP。

升级时会保留已有配置。如果旧安装当前仍显示 `scrapbook`，请在 GsCore 控制台选择 `ATRI`，或执行 `day设置模板 ATRI`；这不是更新失败，而是为了避免覆盖用户主动选择过的模板。

## 丨AI 配置

本插件直接使用自身的 OpenAI 兼容 HTTP Provider，完全不读取早柚核心全局 AI 配置。

1. 打开插件 WebUI 的“配置中心 → LLM 设置”。
2. 填写插件专用 API Key、API 端点 URL 和模型名；端点填写到 `/v1` 根地址即可。
3. 根据服务商能力调整 temperature、最大输出 Token、请求超时、重试和流式开关。
4. 保存配置后，新请求立即使用插件配置；如运行中的任务仍持有旧配置，重载插件后再测试。

API Key 只应保存在本机 `data/DailyAnalyisis/config.json`，不要提交到插件仓库或公开日志。

> [!NOTE]
> 分析模型与绘图模型可以使用同一 API 地址，但绘图模型本身必须支持生图。若服务端对 `/images/generations` 返回“不支持该模型”，或 Chat API 仅返回文本，日报分析仍可正常运行，漫画则不会产生最终图片。

## 丨AstrBot 连接

1. 在 AstrBot 中只启用 `astrbot_plugin_gscore_adapter`，不要再安装原 AstrBot 群分析插件。
2. 将适配器地址设置为 `127.0.0.1`，端口设置为 `8765`。
3. 将适配器的 WebSocket Token 设置为 GsCore `data/config.json` 中的 `WS_TOKEN`。
4. 先启动 GsCore，再启动或重载 AstrBot 适配器；看到 GsCore 的 WebSocket 连接成功日志即完成连接。

群文件夹和群相册上传需要适配器支持受限的 `execute_onebot_action` 上传控制段；普通文本、图片、HTML 文件和合并转发不依赖此扩展。

## 丨WebUI

默认 GsCore 端口为 `8765`；外部 WebUI 默认关闭，开启配置后插件页面地址：

```text
http://127.0.0.1:8765/daily-analyisis-gscore/
```

API 前缀：

```text
/api/daily_analyisis/
```

请求由 GsCore FastAPI 直接处理，WebUI 不依赖任何外部宿主页面桥。

页面首次打开时先设置 WebUI 密码；已经设置过密码时先登录才能进入控制台。密码配置也可以在 GsCore WebConsole 的 `DailyAnalyisis基础配置` 中直接修改。若通过反向代理公网暴露，请同时配置 HTTPS、访问控制和合理的代理超时。

## 丨数据目录

运行数据全部位于 GsCore 的 `data/DailyAnalyisis/`：

- `config.json`：完整插件配置
- `gscore_config.json`：GsCore 配置中心总开关镜像
- `gscore_configs/`：按功能分组的 GsCore 配置中心镜像
- `messages.db`：跨平台群消息存档
- `traces.db`：分析链路与消耗记录
- `reports/`、`tmp/`、`avatar/`：报告、临时文件与头像缓存

这些文件不会写入插件源码目录，也不会被 Git 跟踪。

## 丨启动

在 GsCore 仓库根目录执行：

```sh
uv run core
```

使用当前 Windows 虚拟环境时也可以执行：

```powershell
$env:PYTHONUTF8 = "1"
$env:NO_PROXY = "localhost,127.0.0.1"
.\.venv\Scripts\core.exe
```

看到日志中的 `DailyAnalyisis 就绪` 以及当前消息适配器的连接成功提示后即可在群聊中使用指令。

## 丨实现说明

- GsCore `Plugins` / `SV` 原生注册插件生命周期、消息归档和全部八个命令。
- GsCore `Event` 会被转换为插件统一事件，平台发送由 GsCore `Bot` 完成。
- 配置、持久化、HTML 渲染、Web API 和消息组件均由插件内的 GsCore 运行时实现。
- LLM 调用由插件内置的 OpenAI 兼容 HTTP Provider 执行，不借用其他机器人框架的 Provider 或配置中心。

## 丨感谢

- [SXP-Simon](https://github.com/SXP-Simon) — 原始项目 [astrbot_plugin_qq_group_daily_analysis](https://github.com/SXP-Simon/astrbot_plugin_qq_group_daily_analysis) 的作者与主要维护者。本移植保留原项目 MIT 许可证、业务逻辑、资源和原作者署名。
- [MeowAndy](https://github.com/MeowAndy) — 对本次完整 GsCore 移植的赞助支持。
- [GsCore / 早柚核心](https://github.com/Genshin-bots/gsuid_core) — 插件框架、适配器抽象、调度、WebConsole 与 AI Core。

## 丨许可证

本项目使用 [MIT License](./LICENSE)。原始代码版权归原作者及贡献者所有；GsCore 移植部分由本仓库维护者提供。
