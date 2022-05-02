import os
import re
import json
import time
import nltk
import chardet
import unicodedata

_cur_dir = os.path.split(os.path.abspath(__file__))[0]
root_dir = os.path.split(_cur_dir)[0]

__reg_split_jsonl = re.compile(r'(?<=\})\r?\n?\{')


def get_relative_dir(*args, root=''):
    """ return the relative path based on the root_dir; if not exists, the dir would be created """
    dir_path = root_dir if not root else root
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    for i, arg in enumerate(args):
        dir_path = os.path.join(dir_path, arg)
        if not os.path.exists(dir_path) and '.' not in arg:
            os.mkdir(dir_path)
    return dir_path


def get_relative_file(*args, root=''):
    """ return the relative path of the file based on the root_dir """
    return os.path.join(get_relative_dir(*args[:-1], root=root), args[-1])


def load_json(_path):
    with open(_path, 'rb') as f:
        return json.load(f)


def unicode_to_ascii(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def full_2_half(string):
    ss = []
    for s in string:
        rstring = ""
        for uchar in s:
            inside_code = ord(uchar)
            # 全角空格直接转换
            if inside_code == 12288:
                inside_code = 32

            # 全角字符（除空格）根据关系转化
            elif 65281 <= inside_code <= 65374:
                inside_code -= 65248
            rstring += chr(inside_code)
        ss.append(rstring)
    return ''.join(ss)


def encode_2_utf8(string: str):
    return string.encode('utf-8') if isinstance(string, str) else string


def decode_2_utf8(string):
    if not isinstance(string, bytes):
        return string

    try:
        return string.decode('utf-8')
    except:
        encoding = chardet.detect(string)['encoding']
        if encoding:
            try:
                return string.decode(encoding)
            except:
                pass
        return string


def single(word: str):
    if not word:
        return word

    pos = nltk.pos_tag([word])[0][1]
    if pos != 'NNS':
        return word

    if word.endswith('ies'):
        return word[:-3] + 'y'
    elif word.endswith('es') and len(word) > 4 and word[-4:-2] in ['sh', 'ch']:
        return word[:-2]
    elif word.endswith('es') and len(word) > 3 and word[-3] in 'sx':
        return word[:-2]
    elif word.endswith('es') and len(word) > 3 and word[-3] in ['s']:
        return word[:-2] + 'is'
    elif word.endswith('en'):
        return word[:-2] + 'an'
    elif word.endswith('s'):
        return word[:-1]
    else:
        return word


def plural(word: str):
    if not word:
        return word

    pos = nltk.pos_tag([word])[0][1]
    if pos != 'NN':
        return word

    """ 单词 转 复数 """
    if word[-1] == 'y':
        return word[:-1] + 'ies'
    elif word[-2:] == 'is':
        return word[:-2] + 'es'
    elif word[-1] in 'sx' or word[-2:] in ['sh', 'ch']:
        return word + 'es'
    elif word[-2:] == 'an':
        return word[:-2] + 'en'
    else:
        return word + 's'


def plural_words(words: list):
    length = len(words)
    if not length:
        return []

    elif length == 1:
        return [plural(words[0])]

    else:
        _phrase1 = ' '.join([plural(words[0])] + words[1:])
        _phrase2 = ' '.join(words[:-1] + [plural(words[-1])])
        _phrase3 = ' '.join(list(map(plural, words)))
        return [_phrase1, _phrase2, _phrase3]


def str_2_timestamp(string, _format):
    return time.mktime(time.strptime(string, _format))


def clear_parent_node(d_field_2_value: dict):
    keys = list(d_field_2_value.keys())
    del_keys = []
    for _k in keys:
        if list(filter(lambda x: f'{_k}.' in x, keys)):
            del_keys.append(_k)
    for _k in del_keys:
        del d_field_2_value[_k]
