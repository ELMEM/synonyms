import os
import sys
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

_cur_dir = os.path.split(os.path.abspath(__file__))[0]
_root_dir = os.path.split(_cur_dir)[0]
sys.path.append(_root_dir)

from lib import logs

logs.MODULE = 'Synonyms'
logs.PROCESS = 'Server'

from interfaces.base import app
from interfaces.synonym import synonym

if __name__ == '__main__':
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(app, host='0.0.0.0', port=80)
