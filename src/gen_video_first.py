import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from volcenginesdkarkruntime import Ark
from config.config import ARK_CONFIG


client = Ark(api_key=ARK_CONFIG["api_key"])

duration = 10

if __name__ == "__main__":
    print("----- create request -----")
    resp = client.content_generation.tasks.create(
        model="doubao-seedance-1-0-lite-i2v-250428",
        content=[
            {
                "type": "text",
                "text": "慢慢过渡转场 --dur {}".format(duration)
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "ect.tos-c"
                },
                "role": "first_frame"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seelite_last_frame.jpeg"
                },
                "role": "last_frame"
            }
        ]
    )
    print(resp)