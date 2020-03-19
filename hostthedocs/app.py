import os
from urllib.parse import unquote, quote

from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.routing import Route, Mount
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from . import getconfig
from .filekeeper import delete_files, insert_link_to_latest, parse_docfiles, unpack_project

dirname = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(dirname,'templates'))
static_dir = os.path.join(dirname,'static')

async def hmfd(request):
    if getconfig.auth_token is not None:
        token = request.headers.get('Authorization')
        if getconfig.auth_token != token:
            return PlainTextResponse('',status_code=401)

    if getconfig.readonly:
        return PlainTextResponse('',status_code=403)

    if request.method == 'POST':
        form = await request.form()
        uploaded_file = form.get('filedata')
        if uploaded_file is None:
            return PlainTextResponse('Request is missing a zip/tar file.',status_code=400)
        metadata = dict(form)
        unpack_project(
            uploaded_file,
            metadata,
            getconfig.docfiles_dir
        )
        await uploaded_file.close()
    elif request.method == 'DELETE':
        if getconfig.disable_delete:
            return PlainTextResponse('',status_code=403)
        project_name = unquote(request.query_params.get('name',''))
        if not project_name:
            return PlainTextResponse('Include at least the name of the project',status_code=400)
        version = request.query_params.get('version')
        entire_project = request.query_params.get('entire_project') in ('True','true')
        if version is None and not entire_project:
            return PlainTextResponse('Include a version or specify entire_project',status_code=400)
        delete_files(project_name,version,getconfig.docfiles_dir,entire_project)
    else:
        return PlainTextResponse('',status_code=405)

    return JSONResponse({'success': True})


def home(request):
    projects = parse_docfiles(
        getconfig.docfiles_dir,
        getconfig.docfiles_link_root
    )
    templ = '{}%(project)s/latest'.format(getconfig.public_path)
    insert_link_to_latest(projects, templ)
    params = dict(
        projects=projects,
        request=request,
        **getconfig.renderables
    )
    return templates.TemplateResponse('index.html', params)


def latest(request):
    project = request.path_params['project']
    path = request.path_params.get('path')
    parsed_docfiles = parse_docfiles(
        getconfig.docfiles_dir, 
        getconfig.docfiles_link_root
    )
    proj_for_name = dict((p['name'], p) for p in parsed_docfiles)
    if project not in proj_for_name:
        msg = 'Project %s not found' % project
        return PlainTextResponse(msg,status_code=404)
    latestindex = proj_for_name[project]['versions'][-1]['link']
    if path is not None:
        latestlink = '%s/%s' % (os.path.dirname(latestindex), path)
    else:
        latestlink = latestindex
    fulllink = '/' + latestlink
    return RedirectResponse(url=quote(fulllink))


app = Starlette(debug=getconfig.debug, routes=[
    Route('/{project}/latest/{path}',latest),
    Route('/{project}/latest',latest),
    Route('/hmfd',hmfd,methods=['POST', 'DELETE']),
    Route('/', home),
    Mount('/static', app=StaticFiles(directory=static_dir), name="static"),
])
