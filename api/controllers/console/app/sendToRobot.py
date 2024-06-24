import os
import requests
import json
import threading
import time
import asyncio
import aiohttp
from werkzeug.exceptions import Forbidden, InternalServerError, NotFound
from extensions.ext_database import db
from models.model import AppMode, Conversation, Message
# 定义一个类给外面调用
class SendToRobotInfo:
# 发送消息给机器人
    
    
    def SendMsg(message:Message):
        
        async def async_post(url, data, headers=None):
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status < 300:
                        if response.headers['Content-Type'].startswith('application/json'):
                                    return await response.json()
                        else:
                                text = await response.text()
                                return text
                    else:
                        raise Exception(f"Request failed with status code {response.status}")
        async def SendToRobot(api_key, prefix_code):
            url = 'http://ai.t.vtoone.com/api/v1/chat-messages'
        # url = 'http://10.1.30.43:5001/v1/completion-messages'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                "inputs": {},
                "query": "发送消息："+prefix_code,
                "response_mode": "streaming",
                "conversation_id": "",
                "user": "SystemRobot",
            }
            result  = await async_post(url, data,headers)
            # response.close()


        current_file_path = os.path.abspath(__file__)
        parent_dir = os.path.dirname(current_file_path)
        robotsendingPath = os.path.join(parent_dir, "setting",'robotsending.json')
        target_app_id = message.app_id
        if not message:
            raise NotFound("对应的消息不存在.")
        # try:
        with open(robotsendingPath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            for item in json_data:
                app_id = item["appID"]
                # 判断appid是否匹配
                if app_id!= target_app_id:
                    continue
                api_keys = [key["api_key"] for key in item["serversapikeys"]]
                # 这里通过appid要获取上下文对话
                history_messages = db.session.query(Message).filter(
                Message.conversation_id == message.conversation_id,
                Message.created_at <= message.created_at
                # Message.id != message.id
            ) \
                .order_by(Message.created_at.desc()).limit(3).all()
                #循环遍历history_messages
                
                
                history_messages = list(reversed(history_messages))
                json_dataNew = []
                for msg in history_messages:
                    json_dataNew.append({
                    '问题': msg.query,
                    '答案': msg.answer
                })

                json_string = json.dumps(json_dataNew, ensure_ascii=False)
                #遍历history_messages
                for api_key in api_keys:
                    asyncio.run(SendToRobot(api_key, json_string))
                    # SendToRobot(api_key, json_string)
        # except Exception as e:
        #             raise Exception(e)
                    # raise Exception("发送消息失败")
   