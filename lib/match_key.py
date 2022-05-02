import re

reg_zh = re.compile(r'[\u3400-\u9FFF]')
reg_en = re.compile('[a-zA-Z]+')
reg_list = re.compile('\.list_\d+(?=\.|$)', re.IGNORECASE)
reg_remove_list = re.compile(r'\.list(_\d+)?(?=\.|$)', re.IGNORECASE)

reg_fuhao = re.compile(r'[^\u3400-\u9FFFa-zA-Z0-9]')
reg_space = re.compile(r'\s+')
reg_special_word = re.compile(
    r'(^|\s+|\.|\d+)(normal|normalized|analyzed|range normalized|range|linked|for|resume|of|entity|sys|user|text|beisen|boe|ext|extent|parser|from parser|properties|recruiting|requirement|stage|一[个次只份]|简历|所属)(\s+|\.|\d+$)')

not_allow_last = ['id', 'name', 'day', 'month', 'year', 'iso', 'gte', 'lte', 'low', 'high', 'enum', 'type', 'start',
                  'end', 'list', 'count', 'max', 'min', 'sum', 'avg', 'requirement', 'require', 'range', 'normalize',
                  'normalized']
reg_remove_key = re.compile(r'/.+')

reg_remove_desc1 = re.compile(r'(建议|详见|比如|如|[上下]限[,，])(.+\s*)+$')
reg_remove_desc2 = re.compile(r'(一[个次只份]或多[个次只份]|一[个次只份]|多[个次只份])')
remove_desc_words = ["要求", "列表", "发布人", "stage", "实体", "结构化的", "结构化"]
not_allow_desc = ["名称", "实体", "实体名称", "实体id"]


def tokenize_key(string: str, _dict: dict = {}, keep_dot=False):
    upper_s = ord('A')
    upper_e = ord('Z')
    lower_s = ord('a')
    lower_e = ord('z')
    num_s = ord('0')
    num_e = ord('9')

    words = list(_dict.keys())

    new_string = ''
    length = len(string)
    i = 0

    while i < length:
        c = string[i]
        ord_c = ord(c)

        if keep_dot and c == '.':
            new_string += c
            i += 1
            continue

        skip = False
        for word in words:
            if string[i: i + len(word)].lower() == word.lower():
                new_string += word.lower() + ' '
                i += len(word)
                skip = True
                break

        if skip:
            continue

        if reg_fuhao.search(c):
            # if ord_c < num_s or num_e < ord_c < upper_s or upper_e < ord_c < lower_s or lower_e < ord_c:
            new_string += ' '
            i += 1
            continue

        last_ord = ord(string[i - 1])
        if i > 0 and (lower_s <= last_ord <= lower_e or upper_s <= last_ord <= upper_e) and num_s <= ord_c <= num_e:
            new_string += ' '
            i += 1
            continue

        c = c.lower()
        if upper_s <= ord_c <= upper_e and i > 0 and (lower_s <= last_ord <= lower_e or num_s <= last_ord <= num_e):
            new_string += ' '
        new_string += c

        i += 1

    new_string = reg_space.sub(' ', new_string).strip()
    return new_string


def remove_bracket(string):
    new_string = ''
    bracket_content = ''

    num_bracket = 0
    length = len(string)
    i = 0
    while i < length:
        c = string[i]

        if c in ['(', '（']:
            bracket_content += ' '
            num_bracket += 1
            i += 1
            continue

        elif c in [')', '）']:
            num_bracket -= 1
            if num_bracket == 0:
                i += 1
                continue

        if num_bracket > 0:
            bracket_content += c
            i += 1
            continue
        else:
            new_string += c
            i += 1

    return new_string, bracket_content.strip()


def process_key(_key, keep_dot=False):
    _key, _ = remove_bracket(_key)
    _key = reg_remove_key.sub('', _key)
    _key = tokenize_key(reg_list.sub('.list', _key), keep_dot=keep_dot)
    while _key != reg_special_word.sub(r'\1', _key):
        _key = reg_special_word.sub(r'\1', _key)
    return reg_space.sub(' ', _key).strip()


def get_last_1_key(_key, keep_dot=False):
    if reg_en.search(_key) and '.' not in _key:
        no_list_keys = tokenize_key(_key).split(' ')
    else:
        no_list_keys = reg_remove_list.sub('', _key).split('.')
    last_key = process_key(no_list_keys[-1], keep_dot)

    if last_key not in not_allow_last:
        return last_key
    elif len(no_list_keys) >= 2 and no_list_keys[-2] not in not_allow_last:
        return process_key('.'.join(no_list_keys[-2:]))
    elif len(no_list_keys) >= 3 and no_list_keys[-3] not in not_allow_last:
        return process_key('.'.join(no_list_keys[-3:]))
    else:
        return process_key('.'.join(no_list_keys[-4:]))
