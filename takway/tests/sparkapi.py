from takway.sparkapi_utils import SparkChatClient, SparkRolyPlayingClient
    
def terminal_stream_test():
    #以下密钥信息从控制台获取
    appid = "fb646f00"    #填写控制台中获取的 APPID 信息
    api_secret = "Njc2M2E3Y2FjMDRjMDhjNjViNTYwOTE1"   #填写控制台中获取的 APISecret 信息
    api_key ="f71ea3399c4d73fe3f6df093f7811a0d"    #填写控制台中获取的 APIKey 信息

    spark_client = SparkChatClient(appid, api_secret, api_key, stream_thread_enable=True, debug=True)
    spark_client.run_terminal_chat()

