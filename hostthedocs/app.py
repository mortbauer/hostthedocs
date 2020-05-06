import os
import logging
from urllib.parse import quote
from collections import OrderedDict

from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from fastapi import FastAPI, Depends, UploadFile,status, HTTPException, File, Form, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel


from . import getconfig
from .filekeeper import delete_files, insert_link_to_latest, parse_docfiles, unpack_project

logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(dirname,'templates'))
static_dir = os.path.join(dirname,'static')

app = FastAPI()

app.mount("/static", StaticFiles(directory=static_dir), name="static")

security = OAuth2PasswordBearer(tokenUrl="/token")


def update_projects():
    app.projects = parse_docfiles(
        getconfig.docfiles_dir,
        getconfig.docfiles_link_root,
    )
    logger.debug('public path is %s',getconfig.public_path)
    templ = '{}%(project)s/latest'.format(getconfig.public_path)
    insert_link_to_latest(app.projects, templ)

update_projects()


class Meta(BaseModel):
    name: str
    version: str
    description: str = '' 


def check_access(token:str = Depends(security)):
    if getconfig.auth_token is not None and getconfig.auth_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect token",
        )
    if getconfig.readonly:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )

def get_meta(name:str=Form(...),description:str=Form(...),version:str=Form(...)):
    return Meta(name=name,description=description,version=version)

@app.post('/hmfd',dependencies=[Depends(check_access)])
async def hmfd(metadata=Depends(get_meta),archive:UploadFile=File(...)):
    unpack_project(
        archive,
        metadata,
        getconfig.docfiles_dir
    )
    await archive.close()
    update_projects()
    return {'success': True}

@app.delete('/hmfd',dependencies=[Depends(check_access)])
async def delete_doc(project:str,version:str=None,entire:bool=None):
    if getconfig.disable_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if version is None and not entire:
        raise HTTPException(
            detail='Include a version or specify entire_project',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    delete_files(project,version,getconfig.docfiles_dir,entire_project=entire)
    update_projects()
    return {'success': True}


@app.get('/')
def home(request:Request):
    params = dict(
        projects=app.projects,
        request=request,
        **getconfig.renderables
    )
    return templates.TemplateResponse('index.html', params)

@app.get('/{project}/latest')
@app.get('/{project}/latest/')
@app.get('/{project}/latest/.*')
def latest(request:Request,project:str):
    path = request.url.path.lstrip(f'/{project}/latest/')
    proj_for_name = {p['name']: p for p in app.projects}
    if project not in proj_for_name:
        raise HTTPException(
            detail=f'Project {project} not found',
            status_code=status.HTTP_404_NOT_FOUND
        )
    latestindex = proj_for_name[project]['versions'][-2]['link']
    if path:
        latestlink = '/'.join((os.path.dirname(latestindex), path))
    else:
        latestlink = latestindex
    fulllink = f'{getconfig.public_path}' + latestlink
    return RedirectResponse(url=quote(fulllink))
