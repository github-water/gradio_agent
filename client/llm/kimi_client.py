import time

from openai import OpenAI, RateLimitError
import json

base_url = "https://api.moonshot.cn/v1"
api_key = 'sk-CuMhM6l3BBmnTgRkbwLhDj5SREkk37AiBJjCjD5FM295svnE'

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)


def call_kimi_client(key="sk-CuMhM6l3BBmnTgRkbwLhDj5SREkk37AiBJjCjD5FM295svnE",
                     model="moonshot-v1-32k",
                     user_content="如何做西红柿炖牛腩？",
                     system_content=None):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", "content": system_content
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
                          system_content=system_prompt,
                          retry_times=0):
    try:
        print(f'user_content: {user_content}, system_content: {system_content}')
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", "content": system_content
                },
                {
                    "role": "user", "content": user_content
                }],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except RateLimitError as e:
        if e.status_code == 429 and retry_times <= 3:
            print("Rate limit exceeded. Waiting for 1 second...")
            time.sleep(20)
            return call_kimi_client_json(system_content=system_content, user_content=user_content, retry_times=retry_times+ 1)
        print(f"An AuthenticationError occurred: {e}")
        return None


def multi_round_chat(system_input, user_input, history, retry_times=0):
    try:
        if len(history) == 0:
            history = [{'role': 'system', 'content': system_input}]

        # 将用户的最新问题添加到对话历史中
        history.append({"role": "user", "content": user_input})
        # 请求模型生成回应
        completion = client.chat.completions.create(
            model="moonshot-v1-128k",  # 选择合适的模型
            messages=history,
            temperature=0.5,  # 设置创造性
            response_format={"type": "json_object"}
        )

        # 获取模型的回应并添加到历史中
        response = completion.choices[0].message.content
        history.append({"role": "assistant", "content": response})
        return response, history
    except RateLimitError as e:
        if e.status_code == 429 and retry_times <= 3:
            print("Rate limit exceeded. Waiting for 1 second...")
            time.sleep(20)
            return multi_round_chat(system_input, user_input, history, retry_times + 1)
        print(f"An AuthenticationError occurred: {e}")
        return None, history


if __name__ == "__main__":

    system_prompt = """
                - Role: 文本校对专家和语言润色大师
- Background: 用户需要对小说文本进行优化，以确保语言的流畅性和准确性，同时保持原作的语义和风格。
- Profile: 你是一位经验丰富的文本校对专家，对语言的细微差别有着敏锐的洞察力，擅长在不改变原文意图的前提下，提升文本的可读性和专业性。
- Skills: 你具备深厚的语言功底，能够识别并纠正错别字、语法错误和语义不明确的地方。同时，你能够巧妙地添加或调整标点符号，以增强文本的表达力。
- Goals: 
  1. 识别并纠正文本中的错别字和语法错误。
  2. 优化句子结构，提高文本的流畅性和可读性。
  3. 保持原文的语义和风格，确保优化后的文本忠实于原作。
  4. 添加或调整标点符号，以增强文本的表达效果。
- Constrains: 
  1. 优化过程必须尊重原文的意图和风格。
  2. 避免过度修改，以免破坏原作的韵味。
- Workflow:
  1. 仔细阅读原文，理解作者的意图和文本的风格。
  2. 识别文本中的错别字、语法错误和语义不明确的地方。
  3. 根据语言规范和出版标准，进行适当的文本修改，但不要延伸扩充。
  4. 添加或调整标点符号，以增强文本的表达效果。
  5. 再次审阅修改后的文本，确保所有修改都符合目标和约束。
- Examples:
  - 原文：“他走了很长的路，终于到达了目的地。”
    修改后：“他走了很长的路，终于到达了目的地。”
  - 原文：“她看着窗外，心中充满了期待。”
    修改后：“她凝视着窗外，心中充满了期待。”
请使用如下 JSON 格式输出你的回复：

                    {
                        "text": "修正后的正文"
                    }
                    注意，请将修正后的正文放置在`text`中
            """
    user_prompt = """
        我们村的女子结婚前夜必须去村后的山庙裸睡一夜才能出嫁。只有把初夜交给山神，这样娘家才会平平安安。如果违背这条村规，娘家必有横祸。大学时，我谈了一个男朋友告诉他，我们村这个不成文的规矩，男友自然不信，觉得是我们村里的某个老色胚装神弄鬼，目的就是白嫖姑娘。趁着十一假期，男友决定跟我一起回老家，他要亲自把那老色胚揪出来，并将老色胚绳之以法拯救我们村的未婚女子。
    """
    result = call_kimi_client_json(system_content=system_prompt, user_content=user_prompt)
    print(result['text'])


'''
     system_prompt = """
- Role: 文本校对专家和语言润色大师
- Background: 用户需要对小说文本进行优化，以确保语言的流畅性和准确性，同时保持原作的语义和风格。
- Profile: 你是一位经验丰富的文本校对专家，对语言的细微差别有着敏锐的洞察力，擅长在不改变原文意图的前提下，提升文本的可读性和专业性。
- Skills: 你具备深厚的语言功底，能够识别并纠正错别字、语法错误和语义不明确的地方。同时，你能够巧妙地添加或调整标点符号，以增强文本的表达力。
- Goals: 
  1. 识别并纠正文本中的错别字和语法错误。
  2. 优化句子结构，提高文本的流畅性和可读性。
  3. 保持原文的语义和风格，确保优化后的文本忠实于原作。
  4. 添加或调整标点符号，以增强文本的表达效果。
- Constrains: 
  1. 优化过程必须尊重原文的意图和风格。
  2. 避免过度修改，以免破坏原作的韵味。
- Workflow:
  1. 仔细阅读原文，理解作者的意图和文本的风格。
  2. 识别文本中的错别字、语法错误和语义不明确的地方。
  3. 根据语言规范和出版标准，进行适当的文本修改，但不要延伸扩充。
  4. 添加或调整标点符号，以增强文本的表达效果。
  5. 再次审阅修改后的文本，确保所有修改都符合目标和约束。
- Examples:
  - 原文：“他走了很长的路，终于到达了目的地。”
    修改后：“他走了很长的路，终于到达了目的地。”
  - 原文：“她看着窗外，心中充满了期待。”
    修改后：“她凝视着窗外，心中充满了期待。”
- Initialization: 在第一次对话中，请直接输出以下：您好，我是专业的文本校对和润色专家。请将您的小说文本发给我，我将帮您进行细致的校对和优化，确保文本的准确性和流畅性，同时保持原作的语义和风格。

请使用如下 JSON 格式输出你的回复：

                    {
                        "text": "修正后的正文"
                    }
                    注意，请将修正后的正文放置在`text`中
    """
    user_input_arr = [
        "我奶奶出车祸去世我爸收了肇事者50万成了村里人人羡慕的对象而我在火葬场外亲耳听见肇事者笑着打电话50万搞定性价比还行放心咱们的秘密永远不会有人说出去了出事前半个小时我奶奶给我打过一个电话我没接到当时我正在进行我的研究生面试等我再打回去的时候电话那头已经无人接听不过我没当回事这个小老太太经常这样一进家门眼里就有干不完的活计决想不起来在看手机一眼我以为这次也如寻常的那许多次一样等第二天他出门看到手机的时候自然会给我回电话但第二天我等来的却是我发小周阳的电话他的声音听上去遥远又不切实际小鸭你奶奶出车祸人没了你怎么还不回来是的奶奶去世的消息甚至不是我爸妈告诉我的而是我从同村发小那里得知的我是个留守儿童自小跟奶奶亲近不夸张地说在我爸妈回老家之前我一直以为我奶奶是我妈奶奶去世对我来说无异于五雷轰顶我火急火燎的往回感同时觉得奇怪虽然我跟爸妈关系一向不好但是这么大的事情我爸为什么瞒着不告诉我以为一路上我给我爸打了不下10个电话我爸统统不接直到我回到家里看见院子里已经挂上了白帆做丧事用的那种眼前实实在在的场景让奶奶去世这件事一下子有了真实感我意识到奶奶是真的不在了之后整个人瘫软在地邻居家的婶子扶起我来说好孩子别难受了你奶奶这也算喜丧我不可思议的望着他我奶奶才67是一个走路带风的胡老太太",
        "她死怎么能算喜丧我气愤的望着林家婶子另一个街坊脸上竟然浮出了一层艳羡之色是啊死了还得孙子挣下这么大一笔钱可不是喜丧吗你奶奶真是有命过日子于是我知道了我爸不通知我的原因他是怕我挡了他的财路我想起这几年我爸都是怎么对我的他一直阻止我考研究生他希望我赶紧毕业赶紧工作赶紧找个人结婚好换一笔彩礼你不结婚不要彩礼你弟弟拿什么结婚拿什么付彩礼你做姐姐的不能太自私我不理他他就怪我奶奶说都是奶奶挑唆的闺女跟我们都被亲白养了浑然忘记当初他们把我生下来就把我扔给了我奶奶事实上我爸妈没有亲自抚育过我一天奶奶劝我不要跟我爸计较他就是就是个混人拿你那个笨货弟弟当个大宝贝你别理他咱就好好读书将来出息了气死他们钱的事你也别担心奶奶有钱怎么也能把你供出来奶奶在技校做保洁每个月挣1500块钱她自己吃用500剩下的都给我存起来我当然不要他的钱我上大学起就开始勤工俭学业余还给人写公众号虽然挣的不多但是自己完全够花我奶奶不管他就要把钱攒起来给我你现在花不着我就攒起来留着给你当嫁妆我蒋兰英的大孙女出嫁那可不能没嫁妆让人笑话奶奶的话还在耳边但是他的人却不在了从此这个世界上再也没有一个人会记挂张晓雅是不是缺钱花是不是没嫁妆会不会被人笑话想到这里我再也忍不住嚎啕大哭其实我知道",
        "我爸一直惦记着奶奶的钱只是奶奶一直不给他为此他还跟奶奶大吵大闹过说他里外不分有钱不给孙子花等他死了别怪孙子不给他烧纸什么的现在奶奶真的死了"
    ]
    tmp_history = []
    for user_input in user_input_arr:
        response, tmp_history = multi_round_chat(system_prompt, user_input, tmp_history)
        print(response, tmp_history)
'''

