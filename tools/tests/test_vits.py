
from takway.tests.vits import *


def main():
    speaker_id = 103
    # speaker_id=111 # 成熟甜
    # speaker_id=125  # 成熟深沉
    # speaker_id=132  # 成熟冷酷
    # text = "你好，我是冷白，你找我做什么？"
    text = "当你觉得自己又丑又穷，一无是处时，别绝望，因为...至少你的判断还是对的！！！"
    text = '为什么理发师出门要带水？'
    text = '好呀，你尽管放马过来吧！'
    text = '呦，哈哈，还不错呀，果然和我呆一起久了都变聪明了，嘿嘿。'
    text = '当然是因为托尼带水啦，嘻嘻。看你这么菜，那我问你一个：有一根牙签走在马路上，看见一只刺猬，于是他停下来说什么？'
    test_vits_saver(text, speaker_id)
    print("test_vits_saver passed")
    test_vits_player(text, speaker_id)
    print("test_vits_player passed")



if __name__ == '__main__':
    main()