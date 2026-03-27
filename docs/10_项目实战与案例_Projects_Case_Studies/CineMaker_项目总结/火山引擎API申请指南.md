<!-- 文档同步自 https://github.com/chenweidu666/CineMaker-AI-Platform 分支 main — 请勿手工与上游长期双轨编辑 -->


<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>火山引擎 API 申请与配置指南</strong></div>

CineMaker 的 AI 功能（剧本生成、图片生成、视频生成等）由**火山引擎**提供。
使用前，你需要在火山引擎申请自己的 API 密钥，并在 CineMaker 的设置页面填入。
API 费用由火山引擎直接向你收取，CineMaker 不经手任何费用。


# 1. 你需要准备什么


CineMaker 用到以下火山引擎服务，请按需开通：

| 服务 | 模型 | 用途 | 是否必选 |
|------|------|------|---------|
| 火山方舟（文本） | **Doubao 1.5 Pro** | 剧本生成、分镜拆分、提示词生成、角色/场景/道具提取 | **必选** |
| 火山方舟（图片） | **Seedream 4.0** | 角色三视图、场景 21:9 超宽银幕空镜头、首帧/尾帧图片生成 | **必选** |
| 火山方舟（图片编辑） | **Seededit 3.0** | 图片微调（局部重绘） | **必选** |
| 火山方舟（视频） | **Seedance 1.5 Pro** | 首尾帧视频生成 | **必选** |

> **费用参考**：以一集 13 个镜头、1 分 30 秒的短剧为例，全部 API 调用费用约 **20 元人民币**。建议首次体验先充值 **50 元**。

---


# 2. 注册火山引擎账号


## 2.1. 第一步：注册

访问 [火山引擎官网](https://www.volcengine.com/) ，点击右上角「注册」，使用手机号完成注册。

已有火山引擎账号可直接登录。

## 2.2. 第二步：实名认证

登录后进入 [账号中心](https://console.volcengine.com/user/basics/)，完成**实名认证**：

- 支持**个人认证**和**企业认证**
- **未完成实名认证将无法开通任何 AI 服务**

## 2.3. 第三步：领取免费额度

火山引擎为新用户提供了**免费推理额度**，无需充值即可开始体验：

- **新用户赠送 50 万 tokens** 推理额度，适用于豆包全系模型
- **每日协作奖励**：个人用户每日可领 200 万免费 tokens，企业认证后每日单模型可领 500 万 tokens

进入 [火山方舟 → 开通管理](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement) 页面，在顶部的「领取免费资源包」区域领取：

<div align="center">
<img src="../guides/images/30-volcengine-free-quota.png" alt="火山引擎免费额度 - 新用户赠送 50 万 tokens + 每日协作奖励" width="720">

*▲ **火山引擎免费额度**。新用户赠送 50 万 tokens，协作奖励计划每日最高赠送 500 万 tokens。各模型的免费额度在「开通管理」页面可查看。*
</div>

> **免费额度用完后**：进入 [费用中心](https://console.volcengine.com/finance/overview/) 充值即可继续使用。参考费用：一集 13 镜头短剧约 20 元。

---


# 3. 申请 API 密钥（火山方舟）


火山方舟是火山引擎的大模型服务平台，CineMaker 用到的文本、图片、视频模型都在这个平台上。调用方舟平台模型需使用 API Key 鉴权。

## 3.1. 第一步：获取 API Key

1. 打开并登录 [API Key 管理](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 页面
2. （可选）单击左上角 **账号全部资源** 下拉箭头，切换项目空间
3. 单击 **创建 API Key** 按钮
4. 在弹出框的 **名称** 文本框中确认/更改 API Key 名称（如"CineMaker"），单击创建
5. **立即复制并保存** API Key（UUID 格式）

> **重要**：API Key 创建后只显示一次，请务必立即复制保存到安全的地方。泄露 API Key 会导致模型用量被他人使用产生损失。建议配置到环境变量中而非硬编码进代码。

> **一个 Key 通用**：该 API Key 可同时用于文本、图片、视频所有模型，不需要为每个模型单独创建。

> **说明**：API Key 创建于当前项目空间，仅支持访问该项目下的接入点。主账号下最多可创建 50 个 API Key。

## 3.2. 第三步：开通模型

在火山方舟中，你需要开通以下 4 个模型：

1. 进入 [开通管理 → 视觉模型](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&advancedActiveKey=model&tab=ComputerVision) 页面
2. 搜索并开通以下模型：

| 模型名称 | 用途 | 备注 |
|---------|------|------|
| **Doubao 1.5 Pro** | 文本生成 | 也叫"豆包 1.5 Pro" |
| **Seedream 4.0** | 图片生成 | 搜索 "Seedream" |
| **Seededit 3.0** | 图片编辑 | 搜索 "Seededit" |
| **Seedance 1.5 Pro** | 视频生成 | 搜索 "Seedance" |

3. 每个模型开通后，记下它的 **Model ID**（模型标识符）

> **如何找到 Model ID？** 在模型详情页面或推理接入点列表中可以看到，格式类似 `doubao-1-5-pro-32k-250115`、`seedream-4.0` 等。

## 3.3. 第四步：记录你的配置信息

把以下信息记录下来，后面在 CineMaker 中配置时会用到：

> **推荐**：将 API Key 配置在环境变量中（如 `.env` 的 `TEXT_API_KEY`、`IMAGE_API_KEY`、`VIDEO_API_KEY`），而非硬编码进代码，可避免泄露导致配额被他人使用。参考 `.env.example`。

| 信息 | 值 | 说明 |
|------|------|------|
| **API Key** | 在控制台创建的 API Key | 第二步创建的，所有模型共用 |
| **Base URL** | `https://ark.cn-beijing.volces.com/api/v3` | 固定值，直接复制 |
| **文本模型 ID** | 如 `doubao-1-5-pro-32k-250115` | Doubao 1.5 Pro 的 Model ID |
| **图片模型 ID** | 如 `seedream-4.0` | Seedream 4.0 的 Model ID |
| **图片编辑模型 ID** | 如 `seededit-3.0` | Seededit 3.0 的 Model ID |
| **视频模型 ID** | 如 `doubao-seedance-1-5-pro-251215` | Seedance 1.5 Pro 的 Model ID |

---


# 4. 在 CineMaker 中配置


## 4.1. 进入配置页面

登录 CineMaker 后，点击右上角的用户头像，选择 **「AI 服务配置」** 进入配置页面。

## 4.2. 添加文本服务

点击「添加配置」，按以下内容填写：

| 字段 | 填写内容 |
|------|---------|
| 服务名称 | `火山引擎 - 文本` |
| 服务类型 | 选择 **文本** |
| 供应商 | 选择 **doubao** |
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| API Key | 填入你的 API Key |
| 模型 | 填入文本模型 ID（如 `doubao-1-5-pro-32k-250115`） |
| 设为默认 | **开启** |

> Endpoint 会根据供应商自动填充，无需手动输入。

## 4.3. 添加图片服务

点击「添加配置」，填写：

| 字段 | 填写内容 |
|------|---------|
| 服务名称 | `火山引擎 - 图片` |
| 服务类型 | 选择 **图片** |
| 供应商 | 选择 **doubao** |
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| API Key | 填入你的 API Key（同上） |
| 模型 | 填入图片模型 ID（如 `seedream-4.0`） |
| 设为默认 | **开启** |

> 如果你还需要图片编辑（微调）功能，可以在模型字段中用逗号分隔添加：`seedream-4.0, seededit-3.0`

## 4.4. 添加视频服务

点击「添加配置」，填写：

| 字段 | 填写内容 |
|------|---------|
| 服务名称 | `火山引擎 - 视频` |
| 服务类型 | 选择 **视频** |
| 供应商 | 选择 **doubao** |
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| API Key | 填入你的 API Key（同上） |
| 模型 | 填入视频模型 ID（如 `doubao-seedance-1-5-pro-251215`） |
| 设为默认 | **开启** |

---


# 5. 验证配置


## 5.1. 测试连接

每个服务配置好后，点击配置卡片上的 **「测试连接」** 按钮：

- **成功** — 显示绿色提示，表示 API Key 和模型配置正确
- **失败** — 检查以下几点：
  - API Key 是否复制完整（注意首尾不要有空格）
  - Base URL 是否正确（应该是 `https://ark.cn-beijing.volces.com/api/v3`）
  - 模型是否已在火山方舟中开通
  - 火山引擎账户是否有余额

## 5.2. 实际测试

建议做一次简单的端到端测试：

1. 创建一个短剧项目
2. 添加一个角色，尝试 **AI 生成角色图片** → 验证图片服务
3. 写一段简短剧本，尝试 **AI 分镜拆分** → 验证文本服务
4. 选择一个镜头，尝试 **生成视频** → 验证视频服务

## 5.3. 费用参考

| 操作 | 单次大约费用 |
|------|------------|
| 生成一段剧本 / 分镜拆分 | < 0.1 元 |
| 生成一张图片（角色/场景/首帧/尾帧） | 0.3 - 0.5 元 |
| 图片微调 | 0.2 - 0.3 元 |
| 生成一段视频（5-10 秒） | 1 - 2 元 |
| **一集完整短剧**（13 镜头，约 90 秒） | **约 20 元** |

> 具体价格以 [火山引擎官方定价](https://www.volcengine.com/docs/82379/1544106) 为准。可在火山引擎 [费用中心](https://console.volcengine.com/finance/overview/) 随时查看用量和账单。

---


# 6. 常见问题


## 6.1. "API Key 无效"

- 确认你复制的是**火山方舟**的 API Key（以 `ark-` 开头），不是火山引擎控制台的 AccessKey
- 检查复制时首尾是否有多余的空格
- 如果 Key 丢失了，去火山方舟重新创建一个

## 6.2. "模型未开通"或"模型不存在"

- 确认你在火山方舟的模型广场已经**开通**了对应模型
- 检查 Model ID 是否拼写正确
- 部分模型需要申请才能使用，检查是否有待审批的申请

## 6.3. "余额不足"

- 登录火山引擎 [费用中心](https://console.volcengine.com/finance/overview/) 查看余额
- API 调用需要账户有充足余额，建议保持 50 元以上

## 6.4. "测试连接失败"

- Base URL 必须是 `https://ark.cn-beijing.volces.com/api/v3`，注意 **不要遗漏 `/api/v3`**
- 供应商必须选择 **doubao**（或 volcengine）
- 如果所有检查都没问题，等几分钟后重试（新开通的模型可能需要几分钟生效）

## 6.5. "视频生成一直显示处理中"

- 视频生成通常需要 30-120 秒，请耐心等待
- 如果超过 5 分钟仍未完成，可能是火山引擎服务端繁忙，稍后重试

---


# 7. 附录：火山引擎官方文档


以下链接可以帮助你进一步了解各个模型的能力和使用方法：

| 文档 | 链接 |
|------|------|
| 火山方舟控制台 | [ark.volcengine.com](https://ark.volcengine.com/) |
| Seedance 视频生成教程 | [Seedance SDK 教程](https://www.volcengine.com/docs/82379/1366799) |
| Seedream 图片生成教程 | [Seedream 4.0-4.5 教程](https://www.volcengine.com/docs/82379/1824121) |
| Seedream 提示词指南 | [提示词最佳实践](https://www.volcengine.com/docs/82379/1829186) |
| Seedream + Seedance 最佳实践 | [图生视频最佳实践](https://www.volcengine.com/docs/82379/1951250) |
| 模型列表 | [全部可用模型](https://www.volcengine.com/docs/82379/1799865) |
| 模型定价 | [计费说明](https://www.volcengine.com/docs/82379/1544106) |
| Base URL 与鉴权 | [API 鉴权说明](https://www.volcengine.com/docs/82379/1298459) |
| API Key 管理 | [API Key 管理](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) / [文档](https://www.volcengine.com/docs/82379/1541594) |
