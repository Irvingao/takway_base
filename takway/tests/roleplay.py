from takway.roleplay_utils import SparkRolyPlayingFunction

def test_SparkRolyPlayingFunction():
    character_data_dir = "characters"
    character_name = "Klee_test"
    spark_rpg = SparkRolyPlayingFunction(character_data_dir)
    spark_rpg.set_character(character_name)

    # Generate test prompt
    text = []
    text = spark_rpg.gen_sys_prompt(text)
    text = spark_rpg.gen_user_text(text, "Test user input", prompt_id=1)
    text = spark_rpg.gen_user_text(text, "Another test user input", prompt_id=2)
    

    print("Generated Test Prompt:")
    for prompt in text:
        print(prompt)
    
    print("---------------------------------")
    print("Character Data:")    
    print(spark_rpg.character_info.character_data)
    print(spark_rpg.character_info.character_name)
    print(spark_rpg.character_info.description)
    print(spark_rpg.character_info.list_keys)
    
def test_spark_terminal_roleplay(character_name="Klee_test_v2_en"):
    from takway.sparkapi_utils import SparkRolyPlayingClient
    #以下密钥信息从控制台获取
    appid = "fb646f00"    #填写控制台中获取的 APPID 信息
    api_secret = "Njc2M2E3Y2FjMDRjMDhjNjViNTYwOTE1"   #填写控制台中获取的 APISecret 信息
    api_key ="f71ea3399c4d73fe3f6df093f7811a0d"    #填写控制台中获取的 APIKey 信息

    character_data_dir = "characters"
    # character_name = "Klee_test_v2_en"
    
    spark_client = SparkRolyPlayingClient(appid, api_secret, api_key, 
                                          character_data_dir=character_data_dir,
                                          stream_thread_enable=True, debug=True)
    spark_client.run_roleplay_chat(character_name)

