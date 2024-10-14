import os
import json
import plugins
import logging
import requests 
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from http import HTTPStatus
from dashscope import ImageSynthesis
import re

MODEL = "flux-dev"

@plugins.register(name="AliFlux_Dev",
desc="AliFlux画图插件",
version="1.0",
author="Lingyuzhou",
desire_priority=100)
class AliFluxDev(Plugin):
    RATIO_MAP = {
        "1:1": "1024*1024",
        "1:2": "512*1024",
        "3:2": "768*512",
        "3:4": "768*1024",
        "9:16": "576*1024",
        "16:9": "1024*576"
    }

    # 人设提示词
    SYS_IMAGE_GEN = (
        "You are a powerful Stable Diffusion prompt assistant. You can accurately translate Chinese to English and expand scenes and detailed descriptions based on simple prompts, generating concise and AI-recognizable painting prompts. Your prompts must output a complete English sentence, and the output result is limited to 100 words or less. It should be detailed and complete, including complex details of what is happening in the image. The text should be limited to one scene. Do not delete important details from the user's input information, especially terms related to graphics, details, lighting, quality, resolution, color profiles, image filters, and artist and character names. Do not output any explanatory content that is unrelated to the image prompt."
    )

    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] initialized")
        
        self.config_data = self.load_config_data()  # 加载配置数据

        try:
            with open(os.path.expanduser("~/.dashscope/api_key"), 'r') as file:
                self.api_key = file.read().strip()
                logger.info("API密钥已设置")
        except FileNotFoundError:
            logger.error("未找到API密钥文件，请确保~/.dashscope/api_key存在")
            return

    def load_config_data(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "config.json")  # 修改为当前目录下的config.json
        if not os.path.exists(config_path):
            logger.error("配置文件未找到，请确保config.json存在")
            return {}
        
        with open(config_path, 'r') as file:
            return json.load(file)

    def get_help_text(self, **kwargs):
        help_text = (
            "插件使用指南：\n"
            f"  **生成图片**：输入 \"阿里绘画 [描述]\"，例如：\n"
            f"   - `阿里绘画 一只可爱的猫`\n"
            "   - 您可以使用 `--ar 宽高比` 来指定图片比例，支持的比例有：\n"
            "     `1:1`、`1:2`、`3:2`、`3:4`、`9:16`、`16:9`。\n"
            f"   - 示例：`阿里绘画 美丽的风景 --ar 16:9`\n"
        )
        return help_text

    def extract_image_size(self, prompt: str) -> (str, str):
        match = re.search(r'--ar (\d+:\d+)', prompt)
        if match:
            ratio = match.group(1).strip()
            size = self.RATIO_MAP.get(ratio, "1024*1024")
            prompt = re.sub(r'--ar \d+:\d+', '', prompt).strip()
        else:
            size = "1024*1024"
        logger.debug(f"[{__class__.__name__}] 提取的图片尺寸: {size}")
        return size, prompt

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return
        content = e_context["context"].content.strip()

        if content.startswith("阿里绘画"):
            logger.info(f"[{__class__.__name__}] 收到消息: {content}")
            
            if "--ar" in content:
                parts = content[len("阿里绘画"):].strip().split("--ar")
                if len(parts) < 2:
                    logger.error("输入格式错误，未提供足够的信息。")
                    return
                
                prompt = parts[0].strip()
                ratio = parts[1].strip().split()[0]
            else:
                logger.error("输入格式错误，未提供比例信息。")
                return
            
            prompt = prompt.strip()
            ratio = ratio.strip()

            if ratio not in self.RATIO_MAP:
                logger.error("比例格式错误，应该为可用比例之一：1:1, 1:2, 3:2, 3:4, 9:16, 16:9。")
                return

            # 增强提示词
            enhanced_prompt = self.enhance_prompt(prompt)

            # 返回增强后的提示词
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = f"增强后的提示词: {enhanced_prompt}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

            # 生成图片
            image_url = self.generate_image(enhanced_prompt, ratio)
            if image_url is not None:
                reply = Reply()
                reply.type = ReplyType.IMAGE_URL
                reply.content = image_url
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                reply = Reply()
                reply.type = ReplyType.ERROR
                reply.content = "获取失败,等待修复⌛️"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS

    def enhance_prompt(self, prompt):
        if not self.config_data:
            return prompt  # 如果加载配置失败，返回原始提示

        enhance_prompt_api_url = self.config_data.get('enhance_prompt_api_url', '')
        enhance_prompt_api_key = self.config_data.get('enhance_prompt_api_key', '')
        enhance_model = self.config_data.get('enhance_model', '')

        if not enhance_prompt_api_url or not enhance_prompt_api_key or not enhance_model:
            logger.error("缺少必要的配置项，无法增强提示词")
            return prompt
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {enhance_prompt_api_key}"
        }

        data = {
            "model": enhance_model,
            "messages": [{"role": "user", "content": self.SYS_IMAGE_GEN + "\n" + prompt}],
            "max_tokens": 512
        }

        try:
            response = requests.post(enhance_prompt_api_url, headers=headers, json=data)
            if response.status_code == HTTPStatus.OK:
                enhanced_response = response.json()
                enhanced_prompt = enhanced_response['choices'][0]['message']['content']
                logger.info(f"提示词增强请求成功, 原始提示词: '{prompt}', 增强后的提示词: '{enhanced_prompt}'")
                return enhanced_prompt.strip()
            else:
                logger.error(f"提示词增强请求失败, 状态码: {response.status_code}")
                return prompt
        except Exception as e:
            logger.error(f"提示词增强接口抛出异常:{e}")
            return prompt

    def generate_image(self, prompt, ratio):
        logger.info(f"使用的API密钥: {self.api_key}")

        size = self.RATIO_MAP.get(ratio, "1024*1024")

        try:
            rsp = ImageSynthesis.call(model=MODEL, prompt=prompt, size=size)
            if rsp.status_code == HTTPStatus.OK:
                logger.info(rsp.output)
                for result in rsp.output.results:
                    img_url = result.url
                    logger.info(img_url)
                    return img_url
            else:
                logger.error('请求失败, 状态码: %s, 信息: %s' % (rsp.status_code, rsp.message))
        except Exception as e:
            logger.error(f"接口抛出异常:{e}")
        return None
