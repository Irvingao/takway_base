'''
接口需求：
1. 支持文心、MiniMax、星火、智谱等webAPI的所有model，可以将每个公司的API单独封装成一个类，放在takway/llm/webllms目录下；
2. 可以使用方法查询已支持的model；
3. 需要能和openllm_api调用方法一致/或需要再封装一层顶层接口，可以根据模型选择调用不同的服务。
'''