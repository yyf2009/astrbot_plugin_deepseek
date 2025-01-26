from astrbot.api.all import *
from typing import Optional
import requests
import json
import os

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

@register("deepseek", "YourName", "DeepSeek大模型插件", "1.0.0")
class DeepSeekPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_key = os.getenv("DEEPSEEK_API_KEY")  # 从环境变量获取API KEY
        
    async def call_deepseek(self, prompt: str, session_id: str) -> str:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"调用DeepSeek失败：{str(e)}"

    # 直接指令调用
    @filter.command("deepseek")
    async def deepseek_cmd(self, event: AstrMessageEvent, *, prompt: str):
        """DeepSeek问答指令"""
        if not self.api_key:
            yield event.plain_result("请先配置DEEPSEEK_API_KEY环境变量")
            return
            
        loading = yield event.plain_result("正在查询DeepSeek...")
        
        try:
            response = await self.call_deepseek(prompt, event.session_id)
            yield event.edit_message(loading, response)
        except Exception as e:
            yield event.edit_message(loading, f"请求出错：{str(e)}")

    # 注册为LLM工具
    @llm_tool(name="deepseek_query")
    async def deepseek_tool(
        self,
        event: AstrMessageEvent,
        question: str,
        temperature: Optional[float] = 0.7
    ) -> MessageEventResult:
        """使用DeepSeek回答复杂问题
        
        Args:
            question(string): 需要回答的问题内容
            temperature(number): 创意程度，0-1之间，默认0.7
        """
        if not self.api_key:
            return event.plain_result("API密钥未配置")
            
        response = await self.call_deepseek(question, event.session_id)
        return event.plain_result(f"DeepSeek回答：\n{response}")

    # 自动处理@机器人的消息
    @filter.at_bot()
    async def auto_reply(self, event: AstrMessageEvent):
        """自动响应@机器人的消息"""
        question = event.message_str.strip()
        if not question:
            return
            
        response = await self.call_deepseek(question, event.session_id)
        yield event.chain_result([
            At(qq=event.get_sender_id()),
            Plain("\n"),
            Plain(response)
        ])
