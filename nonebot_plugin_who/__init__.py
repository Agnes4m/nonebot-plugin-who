from nonebot import require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_alconna")
require("nonebot_plugin_saa")
from . import __main__ as __main__  # noqa: E402

# from .config import ConfigModel  # noqa: E402

__version__ = "0.0.1"
__plugin_meta__ = PluginMetadata(
    name="我是谁",
    description="基于宝可梦我是谁，衍生的猜角色小游戏",
    usage="",
    type="application",
    homepage="https://github.com/Agnes4m/nonebot-plugin-who",
    config=None,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={
        "version": __version__,
        "author": ["Agnes4m <Z735803792@163.com>"],
    },
)
