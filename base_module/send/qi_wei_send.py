import base64
import hashlib
from io import BytesIO
import requests
from .Isend import ISend
from .file_enum import FileEnum
import json

# 企业微信发送消息
class QiWeiSend(ISend):
    
    def __init__(self, key: str = None):
        self.key = key
    
    @classmethod
    def build(cls, key: str = None):
        return cls(key=key)
    
    def split_message_by_last_newline(self,message: str, max_len: int):
        """
        超过 max_len 时，从最后一个 \n 切割
        返回 (head, tail)
        """
        if len(message) <= max_len:
            return message, None

        cut = message.rfind('\n', 0, max_len)
        if cut == -1:
            # 找不到换行，只能硬切
            return message[:max_len], message[max_len:]

        return message[:cut], message[cut + 1:]
    
    # 发送md
    def send_md(self, message: str, max_len: int = 2000):
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}"
        headers = {"Content-Type": "application/json"}

        def post(content):
            data = {
                "msgtype": "markdown_v2",
                "markdown_v2": {
                    "content": content
                }
            }
            return requests.post(url, headers=headers, data=json.dumps(data))

        remain = message
        while remain:
            part, remain = self.split_message_by_last_newline(remain, max_len)
            post(part)

    def send_success_md(self, message:str,title:str="执行成功"):
        return self.send_md(f"# ✅ {title}\n{message}")

    def send_error_md(self, message:str,title:str="执行失败"):
        return self.send_md(f"# ❌ {title}\n{message}")

    def send_warning_md(self, message:str,title:str="执行异常"):
        return self.send_md(f"# ⚠️ {title}\n{message}")
    # @别人
    def send_principal(self, principals:list[str]):
        """保存数据的方法，子类必须实现"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}"

        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "msgtype": "text",
            "text": {
                "mentioned_list":principals
            },
        }
        return requests.post(url, headers=headers, data=json.dumps(data))

    # 发送文件
    def send_file(self, file_name:str,file:BytesIO,mime:FileEnum):
        file_name = self._append_ext(file_name,mime)
        """保存数据的方法，子类必须实现"""
        url  = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media"
        url2 = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}"
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "key": self.key,  # 你的 webhook key
            "type": "file"
        }
        files = {
            "media": (
                file_name,    # 上传后的文件名
                file,  # BytesIO 对象也可以
                mime.mime
            )
        }

        ret1 = resp = requests.post(url, params=params, files=files)
        file_id = resp.json().get('media_id')

        if file_id:
            data = {
                "msgtype": "file",
                "file": {
                    "media_id":file_id 
                }
            }
            ret2 = requests.post(url2, headers=headers, data=json.dumps(data))
        
        return [ret1,ret2]

    # 发送图片
    def send_image(self,img:BytesIO):
        """保存数据的方法，子类必须实现"""
        img.seek(0)
        data = img.read()

        b64 = base64.b64encode(data).decode("utf-8")
        md5 = hashlib.md5(data).hexdigest()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.key}"
        payload = {
            "msgtype": "image",
            "image": {
                "base64": b64,
                "md5": md5
            }
        }
        headers = {
            "Content-Type": "application/json"
        }

        resp = requests.post(
            url,
            data=json.dumps(payload, ensure_ascii=False),
            headers=headers,
            timeout=10
        )

        return resp.json()

    def send_png(self, file_name:str,file:BytesIO):
        return self.send_file(file_name,file,FileEnum.PNG)

    def send_xlsm(self, file_name:str,file:BytesIO):
        return self.send_file(file_name,file,FileEnum.XLSM)

    def _append_ext(self, file_name: str, file_enum: FileEnum) -> str:
        ext = file_enum.ext
        if not file_name.lower().endswith(f'.{ext}'):
            return f"{file_name}.{ext}"
        return file_name

    