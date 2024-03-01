import asyncio

# 使用async定义异步函数
async def fetch_data():
    print("开始获取数据")
    await asyncio.sleep(2)  # 模拟IO操作
    print("完成数据获取")
    return {'data': 1}

async def fetch_data2():
    print("开始获取数据2")
    await asyncio.sleep(2)  # 模拟IO操作
    print("完成数据获取2")
    return {'data': 1}

# 使用async定义另一个异步函数，调用上面的异步函数
async def main():
    print("主函数开始")
    result = await fetch_data()  # 等待fetch_data函数完成
    
    result2 = await fetch_data2()  # 等待fetch_data2函数完成
    
    print("主函数结束", result)

# 运行异步主函数
asyncio.run(main())


