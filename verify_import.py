try:
    from cloudmesh.ai.common.sys import is_linux
    print(f"Import successful! Is Linux: {is_linux()}")
except ImportError as e:
    print(f"Import failed: {e}")
