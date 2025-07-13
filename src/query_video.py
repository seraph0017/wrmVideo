import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from volcenginesdkarkruntime import Ark
from config.config import ARK_CONFIG

client = Ark(api_key=ARK_CONFIG["api_key"])

if __name__ == "__main__":
    resp = client.content_generation.tasks.get(
        task_id="cgt-2025****",
    )
    print(resp)