from typing import Any, Union

import httpx
import logging
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.utils.uuid_utils import is_valid_uuid


class WecomGroupBotTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]
                ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
            invoke tools
        """
        content = tool_parameters.get('content', '')
        if not content:
            return self.create_text_message('Invalid parameter content')

        hook_key = tool_parameters.get('hook_key', '')
        # 将hook_key 以| 分割
        hook_keys = hook_key.split('|')
        print(f'123: {hook_keys}')
        # 遍历hook_keys 发送消息
        for hook_key in hook_keys:
            print(f'Sending message to WeCom group bot with hook_key: {hook_key}')
            # 检查hook_key 是否是有效的UUID
            if not is_valid_uuid(hook_key):
                return self.create_text_message(
                    f'Invalid parameter hook_key ${hook_key}, not a valid UUID')

            msgtype = 'text'
            api_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send'
            headers = {
                'Content-Type': 'application/json',
            }
            params = {
                'key': hook_key,
            }
            payload = {
                "msgtype": msgtype,
                "text": {
                    "content": content,
                }
            }

            try:
                res = httpx.post(api_url, headers=headers, params=params, json=payload)
                if res.is_success:
                    logging.info(f"Text message sent successfully, response: {res.text}")
                    # return self.create_text_message("Text message sent successfully")
                else:
                    logging.exception(f"Failed to send the text message, status code: {res.status_code}, response: {res.text}")
            except Exception as e:
                logging.exception("Failed to send message to group chat bot. {}".format(e))
        return self.create_text_message("Text message sent successfully")
