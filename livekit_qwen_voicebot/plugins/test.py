import pkgutil, livekit.plugins
print("plugins content:", list(pkgutil.iter_modules(livekit.plugins.__path__)))

# 尝试查询 base.py
import livekit.plugins.openai as o
print("openai path:", o.__file__)