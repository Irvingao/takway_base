from openai import OpenAI

client = OpenAI(
  api_key="xxx",
#   base_url="http://10.10.42.227:8000/v1"
  # base_url="http://0.0.0.0:22853/v1"
#   base_url="http://0.0.0.0:65528/v1"
  base_url="http://10.10.230.12:22853/v1"
  # base_url="http://10.10.230.12:65528/v1"
  # base_url="http://172.20.2.33:22853/v1"
#   base_url="http://172.20.2.33:65528/v1"
  # base_url="http://42.247.69.99:22853/v1"
#   base_url="http://42.247.69.99:65528/v1"
)

private_ip = "172.20.2.33"
public_ip = "42.247.69.99"
# 服务器端口
# - 内部端口号：65528
# - 外部端口号：22853

def get_completion(prompt, model="internlm2-chat-1_8b", stream=False, **kwargs):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream,
        temperature=0.7,
        **kwargs
    )
    return response

prompt = "你好，浦语！"

print(get_completion(prompt).choices[0].message.content)

stream = get_completion(prompt, stream=True)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
