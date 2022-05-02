from typing import Optional, List
from pydantic import BaseModel, Field
from interfaces.base import app, o_schema
from lib import logs


class TextInput(BaseModel):
    texts: List[str] = Field(description='需要获取同义词的文本')
    recur_syn: bool = Field(False, description='递归查找同义词')


class Response(BaseModel):
    ret: int = Field(1, description="是否成功；成功为1，失败为0")
    msg: Optional[str] = Field('', description="错误信息；若 ret = 1，则为空")
    synonyms: Optional[List[List[str]]] = Field(description='查询到的同义词')


@app.post('/v1/synonym',
          name="v1 synonym",
          response_model=Response,
          description="查询同义词")
def synonym(_input: TextInput):
    log_id = logs.uid()
    logs.add(f'{log_id}', f'POST {logs.fn_name()}', f'payload: {_input}')

    texts = _input.texts
    recur_syn = _input.recur_syn

    # 检查参数
    if not texts:
        return logs.ret(log_id, logs.fn_name(), 'GET', {'ret': 0, 'msg': 'texts 不能为空'})

    synonyms = list(map(lambda x: o_schema.get_synonym(x, _more_zh=True, _recur_syn=recur_syn), texts))
    return logs.ret(log_id, logs.fn_name(), 'GET', {'ret': 1, 'synonyms': synonyms})
