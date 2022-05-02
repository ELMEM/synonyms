import os
import re
from lib import utils
from lib.match_key import process_key, get_last_1_key, reg_zh, reg_en

_cur_dir = os.path.split(os.path.abspath(__file__))[0]


class Schema:
    _synonym_path = utils.get_relative_file('config', 'synonyms.json')
    _synonym_entire_key_path = utils.get_relative_file('config', 'synonyms_entire_key.json')
    _synonym_full_key_path = utils.get_relative_file('config', 'synonyms_full_key.json')
    _synonym_zh_path = utils.get_relative_file('config', 'synonyms_zh.json')

    _suffix_key_path = utils.get_relative_file('config', 'suffix_key.json')
    _suffix_desc_path = utils.get_relative_file('config', 'suffix_desc.json')

    _remove_end_key_path = utils.get_relative_file('config', 'remove_end_key.json')

    def __init__(self):
        self._reg_phrases = self._get_phrases(utils.load_json(self._synonym_path), is_en=True)
        self._reg_phrases_entire_key = self._get_phrases(utils.load_json(self._synonym_entire_key_path), is_en=True,
                                                         prefix=r'(^|\.)', suffix=r'(?=\.|$)')
        self._reg_phrases_full_key = self._get_phrases(utils.load_json(self._synonym_full_key_path), is_en=True,
                                                       prefix=r'^', suffix=r'$')
        self._reg_phrases_zh = self._get_phrases(utils.load_json(self._synonym_zh_path), is_en=False)

        self._reg_end_phrases = self._get_phrases(utils.load_json(self._remove_end_key_path), is_en=True,
                                                  prefix=r'(?<=[\u3400-\u9FFF\s])', suffix=r'$')

        self._reg_end_key_suffixes = self._init_suffix_dict(
            utils.load_json(self._suffix_key_path), self._reg_phrases, is_en=True)
        self._reg_end_desc_suffixes = self._init_suffix_dict(
            utils.load_json(self._suffix_desc_path), self._reg_phrases_zh, is_en=False)

    @staticmethod
    def _init_suffix_dict(d_key_2_suffix, _reg_phrases, is_en=True):
        reg_end_suffixes = []
        for k, suffixes in d_key_2_suffix.items():

            has_match = False
            for val in _reg_phrases:
                reg = val['reg']
                if not reg.search(k):
                    continue

                pattern = reg.pattern
                if is_en:
                    pattern = pattern.replace(r'(?=\s|$)', '').replace('(^|\s+)', '')
                new_reg = re.compile(f'{pattern}$')
                if not new_reg.search(k):
                    continue

                reg_end_suffixes.append({'reg': new_reg, 'suffix': suffixes})
                has_match = True

            if not has_match:
                new_reg = re.compile(f'{k}$', re.IGNORECASE)
                reg_end_suffixes.append({'reg': new_reg, 'suffix': suffixes})

        return reg_end_suffixes

    @staticmethod
    def _get_phrases(_list_list_phrases, is_en=True, suffix='', prefix=''):
        ret_phrases = []
        prefix = r'(^|\s+)' if is_en and not prefix else prefix
        suffix = r'(?=\s|$)' if is_en and not suffix else suffix

        for _i, _list_phrase in enumerate(_list_list_phrases):
            _reg_list_phrase = _list_phrase['reg']
            _list_sub = _reg_list_phrase if _list_phrase['sub'] == '*' else _list_phrase['sub']
            _zh_phrase = list(filter(lambda x: reg_zh.search(x) or not x, _list_sub))
            _en_phrase = list(filter(lambda x: not reg_zh.search(x), _list_sub))

            _new_phrases = []
            if is_en:
                for _phrase in _reg_list_phrase:
                    if reg_zh.search(_phrase):
                        continue

                    _words = _phrase.split(' ')
                    _single_words = list(map(utils.single, _words))

                    _new_phrases.append(' '.join(_single_words))
                    _new_phrases += utils.plural_words(_single_words)

            _reg_list_phrase = list(set(_reg_list_phrase + _new_phrases))
            _reg_list_phrase = list(map(
                lambda x: x.replace('(', r'\(').replace(')', r'\)'),
                _reg_list_phrase
            ))
            _reg_list_phrase = list(filter(lambda x: x, _reg_list_phrase))
            _reg_list_phrase.sort(key=lambda x: -len(x))

            _reg_list_phrase = '|'.join(_reg_list_phrase)
            _reg_list_phrase = re.compile(f'{prefix}({_reg_list_phrase}){suffix}', re.IGNORECASE)

            ret_phrases.append({'reg': _reg_list_phrase, 'phrases': _en_phrase, 'zh_phrases': _zh_phrase})

        return ret_phrases

    def get_synonym(self, origin_phrase, _more_zh=False, _recur_syn=False):
        _phrase = process_key(origin_phrase)
        _phrase = _phrase if _phrase else origin_phrase
        synonyms = self.get_synonym_key(_phrase, _more_zh) + self.get_synonym_desc(_phrase)

        if _recur_syn and not reg_zh.search(_phrase):
            zh_synonyms = list(filter(lambda x: not reg_en.search(x) and reg_zh.search(x), list(set(synonyms))))
            if zh_synonyms:
                for zh_phrase in zh_synonyms:
                    synonyms += list(filter(lambda x: not reg_en.search(x), self.get_synonym_desc(zh_phrase)))

        _last_word = get_last_1_key(origin_phrase)
        if _last_word != _phrase:
            synonyms += self.get_synonym_key(_last_word, _more_zh) + self.get_synonym_desc(_last_word)

        synonyms = list(set(synonyms))
        synonyms.sort()

        return synonyms

    def get_synonym_key(self, _phrase, _more_zh=False):
        synonyms = [_phrase]

        for val in self._reg_end_key_suffixes:
            reg = val['reg']
            if not reg.search(_phrase):
                continue

            for suffix in val['suffix']:
                if _phrase.endswith(suffix):
                    continue
                synonyms.append(f'{_phrase} {suffix}')

        for val in self._reg_end_phrases:
            reg = val['reg']
            if not reg.search(_phrase):
                continue
            synonyms.append(reg.sub('', _phrase).strip())

        synonyms = list(set(synonyms))

        for val in self._reg_phrases + self._reg_phrases_entire_key + self._reg_phrases_full_key:
            reg = val['reg']
            if not reg.search(_phrase):
                continue

            sub_phrases = val['phrases'] + val['zh_phrases']
            for phrase in sub_phrases:
                ret_search = reg.search(_phrase)
                if ret_search and len(ret_search.group()) == 1 and len(_phrase) > 1:
                    continue
                synonyms.append(reg.sub(f' {phrase}', _phrase).strip())

        if _more_zh:
            zh_keys = [_phrase]
            for val in self._reg_phrases + self._reg_phrases_entire_key:
                reg = val['reg']

                new_keys = []
                for k in zh_keys:
                    if not reg.search(k):
                        new_keys.append(k)
                        continue

                    sub_phrases = val['zh_phrases']
                    if not sub_phrases:
                        new_keys.append(k)
                        continue

                    for phrase in sub_phrases:
                        new_keys.append(reg.sub(f' {phrase}', k).replace('.', ' ').strip())

                zh_keys = new_keys
            synonyms += zh_keys

        synonyms = list(filter(lambda x: x, synonyms))
        return list(set(synonyms))

    def get_synonym_desc(self, _phrase):
        synonyms = [_phrase]

        for val in self._reg_end_desc_suffixes:
            reg = val['reg']
            if not reg.search(_phrase):
                continue

            for suffix in val['suffix']:
                if _phrase.endswith(suffix):
                    continue
                synonyms.append(f'{_phrase}{suffix}')

        synonyms = list(set(synonyms))

        for val in self._reg_phrases_zh:
            reg = val['reg']
            if not reg.search(_phrase):
                continue

            sub_phrases = val['phrases'] + val['zh_phrases']
            for phrase in sub_phrases:
                ret_search = reg.search(_phrase)
                if ret_search and len(ret_search.group()) == 1 and len(_phrase) > 1:
                    continue
                synonyms.append(reg.sub(phrase, _phrase).strip())

        synonyms = list(filter(lambda x: x, synonyms))
        return list(set(synonyms))


if __name__ == '__main__':
    o_schema = Schema()
    phrases = o_schema.get_synonym('WorkExperienceLocationsNormalizedCity',
                                   _more_zh=True, _recur_syn=True)
    for v in phrases:
        print(v)
