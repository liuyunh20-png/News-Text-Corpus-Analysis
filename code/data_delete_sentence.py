original_file = "data_switch_into_txt.txt"

new_file = "data_delete_sentence.txt"

with open(original_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 过滤规则：
# 1. 不以@chinadaily.com.cn结尾
# 2. 不以contributed to this story.结尾
# 3. 不以The author is开头
# 4. 不以Contact the writers at开头
# 5. 不包含The views do not necessarily reflect those of China Daily.
# 6. 不包含Contact the editor at editor@chinawatch.cn.
filtered = [
    line for line in lines
    if not (
        line.rstrip().endswith("@chinadaily.com.cn") or
        line.rstrip().endswith("contributed to this story.") or
        line.rstrip().endswith("@chinadailyusa.com") or
        line.lstrip().startswith("The author is") or
        line.lstrip().startswith("Contact the writers at") or
        "The views do not necessarily reflect those of China Daily." in line.rstrip() or
        "Contact the editor at editor@chinawatch.cn." in line.rstrip() or
        "The views don't necessarily reflect those of China Daily." in line.rstrip() or
        "If you have a specific expertise, or would like to share your thought about our stories, then send us your writings at opinion@chinadaily.com.cn, and comment@chinadaily.com.cn." in line.rstrip()
    )
]


with open(new_file, 'w', encoding='utf-8') as f:
    f.writelines(filtered)