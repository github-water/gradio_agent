from openai import OpenAI
import json


base_url = "https://api.moonshot.cn/v1"

def call_kimi_client(key="sk-CuMhM6l3BBmnTgRkbwLhDj5SREkk37AiBJjCjD5FM295svnE",
                    model="moonshot-v1-32k",
                    user_content="如何做西红柿炖牛腩？",
                    system_content=None):
    client = OpenAI(
        api_key=key,
        base_url=base_url,
    )
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system","content": system_content
            },
            {
                "role": "user", "content": user_content
            }]
    )
    return completion.choices[0].message.content


system_prompt = """
你是月之暗面（Kimi）的智能客服，你负责回答用户提出的各种问题。请参考文档内容回复用户的问题，你的回答可以是文字、图片、链接，在一次回复中可以同时包含文字、图片、链接。

请使用如下 JSON 格式输出你的回复：

{
    "text": "文字信息"
}

注意，请将文字信息放置在 `text` 字段中，将图片以 `oss://` 开头的链接形式放在 `image` 字段中，将普通链接放置在 `url` 字段中。
"""

def call_kimi_client_json(key="sk-CuMhM6l3BBmnTgRkbwLhDj5SREkk37AiBJjCjD5FM295svnE",
                    model="moonshot-v1-32k",
                    user_content="如何做西红柿炖牛腩？",
                    system_content=system_prompt):
    client = OpenAI(
        api_key=key,
        base_url=base_url,
    )
    print(f'user_content: {user_content}, system_content: {system_content}')
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system","content": system_content
            },
            {
                "role": "user", "content": user_content
            }],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)



if __name__ == "__main__":
    system_prompt = """
                你是一个小说家，请审阅上述文本，不改变原文基础上，修正原文不规范的停顿符号和错别字，并进行输出
                请使用如下 JSON 格式输出你的回复：

                {
                    "text": "修正后原文"
                }
                注意，请将修正后原文放置在 `text` 字段中
            """
    user_prompt = """
        我们村的女子结婚前夜必须去村后的山庙裸睡一夜才能出嫁。只有把初夜交给山神，这样娘家才会平平安安。如果违背这条村规，娘家必有横祸。大学时，我谈了一个男朋友告诉他，我们村这个不成文的规矩，男友自然不信，觉得是我们村里的某个老色胚装神弄鬼，目的就是白嫖姑娘。趁着十一假期，男友决定跟我一起回老家，他要亲自把那老色胚揪出来，并将老色胚绳之以法拯救我们村的未婚女子。
    """
    result = call_kimi_client_json(system_content=system_prompt, user_content=user_prompt)
    print(result['text'])