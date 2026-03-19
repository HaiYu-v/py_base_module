import json


class JsonUtil:

    @staticmethod
    def extract_json(text: str):
        """
        从字符串中提取第一个合法 JSON（对象或数组）
        """

        start = None
        stack = []

        for i, char in enumerate(text):
            # 找到 JSON 开始
            if start is None:
                if char in "{[":
                    start = i
                    stack.append("}" if char == "{" else "]")
            else:
                # 匹配结束括号
                if char in "{[":
                    stack.append("}" if char == "{" else "]")
                elif char in "}]":
                    if not stack or char != stack[-1]:
                        # 括号不匹配
                        return None
                    stack.pop()
                    if not stack:
                        # 找到完整 JSON
                        json_str = text[start:i+1]
                        try:
                            return json.loads(json_str)
                        except Exception:
                            return None

        return None