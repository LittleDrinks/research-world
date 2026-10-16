import json
import time
import uuid

import httpx

from .protocol import BASE_INSTRUCTIONS, RESEARCH_INSTRUCTIONS, prediction, save


class Product:
    def __init__(self, url, runtime_url, model, thinking, timeout):
        self.http = httpx.Client(base_url=url.rstrip('/'), timeout=30)
        self.runtime = httpx.Client(base_url=runtime_url.rstrip('/'), timeout=30)
        self.model, self.thinking, self.timeout = model, thinking, timeout

    def request(self, method, path, body=None):
        response = self.http.request(method, '/api/v1'+path, json=body)
        response.raise_for_status()
        return response.json() if response.content else None

    def profile(self, arm, run_id):
        agent_id = f'scifact-{run_id}-{arm}'
        tools = [] if arm == 'baseline' else ['graph','record','connect','delegate']
        spec = {'id':agent_id,'name':agent_id,'model':self.model,'thinking':self.thinking,
                'instructions':BASE_INSTRUCTIONS+(RESEARCH_INSTRUCTIONS if arm=='research' else ''),
                'tools':tools,'skills':[]}
        self.request('PUT', '/agents/'+agent_id, spec)
        return spec

    def run_case(self, task, agent, folder):
        folder.mkdir()
        result = {'id':task['id'],'status':'runtime_failed','prediction':{'id':task['id'],'evidence':{}}}
        started = time.monotonic()
        try:
            root = self._start(task, agent, result, folder)
            detail = self._wait(root)
            save(folder/'detail.json', detail)
            self._answer(task, detail, result, folder)
        except (httpx.HTTPError, TimeoutError, ValueError) as error:
            result['error'] = type(error).__name__ + ': ' + str(error)[:300]
            self._cancel(result)
        result['seconds'] = round(time.monotonic()-started,3)
        self._export(result, folder)
        save(folder/'result.json', result)
        return result

    def _start(self, task, agent, result, folder):
        project = self.request('POST','/projects',{'name':f'{agent}-{task["id"]}', 'question':task['claim']})
        result['project_id'] = project['id']
        body = {'agent_id':agent,'content':json.dumps(task,ensure_ascii=False),'message_id':uuid.uuid4().hex}
        save(folder/'input.json',body)
        session = self.request('POST',f'/projects/{project["id"]}/sessions',body)
        result.update(session_id=session['session']['id'],turn_id=session['turn']['id'])
        save(folder/'started.json',result)
        return f'/projects/{project["id"]}/sessions/{result["session_id"]}'

    def _wait(self, root):
        deadline = time.monotonic()+self.timeout
        while time.monotonic()<deadline:
            detail = self.request('GET',root)
            if detail['run']['turns'][-1]['status']!='running':
                return detail
            time.sleep(1)
        raise TimeoutError('Per-case wall-time limit reached')

    def _answer(self, task, detail, result, folder):
        turn = detail['run']['turns'][-1]
        text = turn['result_text'] or ''
        (folder/'answer.txt').write_text(text)
        result['turn_status'] = turn['status']
        if turn['status']!='completed':
            return
        try:
            result['prediction'] = prediction(text,task)
            result['status'] = 'completed'
        except (ValueError,TypeError,KeyError):
            result['status'] = 'invalid_output'

    def _cancel(self, result):
        if not result.get('turn_id'):
            return
        root = f'/projects/{result["project_id"]}/sessions/{result["session_id"]}/turns/{result["turn_id"]}'
        try:
            self.request('POST',root+'/cancel')
        except httpx.HTTPError:
            result['cancel_failed'] = True

    def _export(self, result, folder):
        if not result.get('session_id'):
            return
        for kind, prefix in [('trajectory',''),('title_trajectory','title-')]:
            try:
                path=f'/api/v1/runtime/sessions/{prefix}{result["session_id"]}/export'
                response=self.runtime.get(path)
                response.raise_for_status()
                save(folder/f'{kind}.json',response.json())
            except httpx.HTTPError:
                result[kind+'_missing']=True
        result.update(input_tokens=None,output_tokens=None,cost=None)
