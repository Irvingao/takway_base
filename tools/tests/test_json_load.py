import json
import io
file = open(r"G:\WorkSpace\CodeWorkspace\GPT_projects\temp_str.txt", 'r', encoding='utf-8')
content = []
for line in file.readlines():
    content.append(line)
file.close()

str_data = ''.join(content)
content =[]
io_str = io.StringIO(str_data)

dict = json.loads(line)
print(type(dict))
print(dict)
print(dict['meta_info'])
