import os
import requests

VK_API_URL = "https://api.vk.com/method/wall.post"
VK_API_VERSION = "5.199"

TOKEN = os.environ.get("VK_ACCESS_TOKEN", "vk1.a.dcbe0SeiPLJm03gsjacx5CIGrBFQajoS7LUb2wJPOSpGXfslxFDUGF8AQlep7okZK_y5A9uGINr8sE0xu8OMuzoBxiXK_B7CRZft0A7o_uuHNuWVRhYcpFlEMuIZTmudgad6jCMHXexc3XiTYL6j23nyxxVFQUGauIBpNOOSebbAtxu7Yp8gLl7k5Lp5TLCi0jVU7dpsr7a1FKvH7P4iow")
GROUP_ID = os.environ.get("VK_GROUP_ID", "239442586")


def is_configured():
    return bool(TOKEN and GROUP_ID)


def post_to_vk(title, content, post_url=None):
    if not is_configured():
        return None

    max_len = 8000
    msg = f"{title}\n\n{content}"[:max_len]
    if len(f"{title}\n\n{content}") > max_len:
        msg += "\n\n... (продолжение на сайте)"

    if post_url:
        msg += f"\n\nЧитать полностью: {post_url}"

    owner_id = -abs(int(GROUP_ID))

    try:
        resp = requests.post(VK_API_URL, data={
            "access_token": TOKEN,
            "owner_id": owner_id,
            "message": msg,
            "from_group": 1,
            "v": VK_API_VERSION,
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return None
        return data.get("response", {})
    except Exception:
        return None
