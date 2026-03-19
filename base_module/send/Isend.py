from abc import ABC, abstractmethod

# 发送消息的接口
class ISend(ABC):
    
    @abstractmethod
    def send_md(self, message:str):
        """获取数据的方法，子类必须实现"""
        pass

    @abstractmethod
    def send_file(self, file, file_name:str):
        """保存数据的方法，子类必须实现"""
        pass

    # @别人
    @abstractmethod
    def send_principal(self, principals:list[str]):
        """保存数据的方法，子类必须实现"""
        pass