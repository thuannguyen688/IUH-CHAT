# from .dashboard.manage import show_manage
# from .dashboard.upload import show_upload
# from .chat.chat import show_chat
# from .home.home import show_home
#
# __all__ = ["show_manage", "show_collections", "show_upload", "show_chat", "show_home"]
from .dashboard import Collections, Manager, Upload
from .chat import Chat
from .login import Login
from .home import  Home
__all__ = ["Collections", "Manager", "Upload", "Chat", 'Login', "Home"]
