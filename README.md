# ali_flux_dev
ali_flux_dev是一款适用于chatgpt-on-wechat 的绘图插件，调用阿里云百炼的API基于FLUX.1 [dev]模型进行文生图。FLUX.1 [dev] 是一款面向非商业应用的开源权重、精炼模型。FLUX.1 [dev] 在保持了与FLUX专业版相近的图像质量和指令遵循能力的同时，具备更高的运行效率。相较于同尺寸的标准模型，它在资源利用上更为高效。

阿里云目前对于个人用户提供1000次免费调用，有效期截止到 2025-02-03。相对于许多收费的API来说，算是比较大的一波福利了。

# 插件使用教程
阿里云的图片生成API调用方式采用的是ImageSynthesis.async_call函数，它不是 Python 标准库中的函数，因此操作起来比一般的API调用要麻烦一点。

使用该插件的前提条件（详见阿里云百炼官方API文档）：https://bailian.console.aliyun.com/?accounttraceid=73d51cc1708e4ea88fd90c654e118f0buonj#/model-market/detail/flux-dev

1）已开通服务并获得API-KEY；2）配置API-KEY到环境变量；3）已安装SDK。

# 一. 安装SDK
SDK是“软件开发工具包”（Software Development Kit）的缩写。它是一组工具、库和文档，帮助开发者创建软件应用程序。

正常情况下在你的cow项目部署之初就应该已经完成了SDK的安装，所以此处略过。

# 二. 获取API-KEY
首先登录阿里云百炼账号，访问阿里云百炼模型体验页面，点击右上角钥匙🔑标志，选择创建API-KEY，复制下来备用。

模型体验网址 https://bailian.console.aliyun.com/?accounttraceid=73d51cc1708e4ea88fd90c654e118f0buonj#/efm/model_experience_center/vision?currentTab=imageGenerate

# 三. 配置API-KEY到环境变量
高手可直接按照官方教程操作
https://help.aliyun.com/zh/model-studio/developer-reference/configure-api-key-through-environment-variables?spm=a2c4g.11186623.0.i1

如果你跟我一样是代码小白，建议按照以下步骤操作，以下命令均在服务器的终端执行。（看起来很复杂，实际上一点也不难）

# 【配置环境变量】
在项目文件夹中添加 ~/.dashscope/api_key 文件路径，具体操作步骤如下：

1. 创建目录:
首先在终端中创建 ~/.dashscope 文件目录，使用以下命令：
mkdir -p ~/.dashscope

2. 创建 API 密钥文件:
在 ~/.dashscope 目录中创建一个名为 api_key 的文件。使用以下命令：
touch ~/.dashscope/api_key

3. 编辑文件:
如果没有安装nano 编辑器，在终端中输入以下命令行完成安装即可：sudo yum install nano
使用文本编辑器（如 nano、vim 或者你喜欢的编辑器）打开 api_key 文件，并在文件中添加你的 API 密钥。假设你的 API 密钥是 your_api_key_here，在终端执行以下命令：
echo "your_api_key_here" > ~/.dashscope/api_key（将"your_api_key_here" 替换成你在官网创建的API-KEY）

4. 验证密钥文件是否创建成功:
继续在终端中输入: nano ~/.dashscope_api_key 并按下 Enter。
如果文件不存在，nano 将会创建一个新文件。如果文件已经存在，它将打开该文件供您编辑。
 Ctrl + O保存➡️Enter确认保存➡️按 Ctrl + X 退出 nano 编辑器。

5. 在代码中指定文件路径:
在你的代码中，确保设置 dashscope.api_key_file_path 为你刚刚创建的文件路径。可以在相关的配置文件中添加如下代码：
dashscope.api_key_file_path = '~/.dashscope/api_key'
这一步已经写在了插件代码中，用户无需操作。

6. 使用环境变量:
在终端中运行以下命令：
export DASHSCOPE_API_KEY_FILE_PATH=~/.dashscope/api_key
这将会在当前终端会话中设置环境变量，服务器重启之后需要重新手动运行。

# 【通过shell文件自动加载环境变量】
将设置环境变量的命令添加到 shell文件中，这样每次启动终端时会自动加载而无需手动运行，具体操作步骤如下：

1. 确定使用的 Shell:
首先，你需要确认你使用的是哪种 shell。常见的 shell 有 Bash 和 Zsh。你可以通过在终端中输入以下命令来查看当前使用的 shell：
echo $SHELL
如果输出的结果包含 bash，那么你使用的是 Bash；如果包含 zsh，那么你使用的是 Zsh。

2. 编辑配置文件:
根据你使用的 shell，选择相应的配置文件进行编辑：
Bash: 编辑 ~/.bashrc 或 ~/.bash_profile 文件
Zsh: 编辑 ~/.zshrc 文件
编辑 Bash 配置文件
如果你使用的是 Bash，执行以下命令打开 ~/.bashrc 文件：
nano ~/.bashrc
或者如果你使用的是 ~/.bash_profile，可以使用：
nano ~/.bash_profile
编辑 Zsh 配置文件
如果你使用的是 Zsh，执行以下命令打开 ~/.zshrc 文件：
nano ~/.zshrc

3. 添加环境变量:
在打开的文件中，向文件的末尾添加以下行：
export DASHSCOPE_API_KEY_FILE_PATH=~/.dashscope/api_key

4. 保存并退出:
如果你使用的是 nano 编辑器，按 Ctrl + O 保存文件，然后按 Enter 确认，最后按 Ctrl + X 退出。
如果你使用的是 vim 编辑器，可以按 Esc，然后输入 :wq 并按 Enter 保存并退出。

5. 使配置生效:
为了使更改立即生效，你可以在终端中运行以下命令，或者重新打开一个终端窗口：
source ~/.bashrc
或者，如果你编辑的是 ~/.bash_profile：
source ~/.bash_profile
或者，如果你编辑的是 ~/.zshrc：
source ~/.zshrc

6. 验证环境变量:
你可以通过以下命令验证环境变量是否设置成功：
echo $DASHSCOPE_API_KEY_FILE_PATH
如果输出为 ~/.dashscope/api_key，说明设置成功。

# 四. 安装插件和配置config文件
1.在微信机器人聊天窗口输入命令：#installp https://github.com/Lingyuzhou111/ali_flux_dev.git

2.在微信机器人聊天窗口输入#scanp 命令扫描新插件是否已添加至插件列表

3.进入config文件配置用来增强提示词的model、api_url、api_key，这个比较简单就不赘述了。

4.重启chatgpt-on-wechat项目，如果同时出现以下提示：

[INFO][2024-10-14 22:04:07][plugin_manager.py:41] - Plugin AliFlux_Dev_v1.0 registered, path=./plugins/ali_flux_dev

[INFO][2024-10-14 22:04:07][ali_flux_dev.py:33] - [AliFluxDev] initialized

[INFO][2024-10-14 22:04:07][ali_flux_dev.py:40] - API密钥已设置

那么恭喜你插件安装成功,赶紧来体验白嫖的乐趣吧！

