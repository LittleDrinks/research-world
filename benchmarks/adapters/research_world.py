"""Execute research tasks through the product, independently of benchmark protocols."""
import json
import time
import uuid

import httpx


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


class ResearchWorld:
    def __init__(self, url, runtime_url, timeout=180, transport=None):
        self.http = httpx.Client(base_url=url.rstrip('/'), timeout=30, transport=transport)
        self.runtime = httpx.Client(base_url=runtime_url.rstrip('/'), timeout=30, transport=transport)
        self.timeout = timeout
        self._cancelled = set()

    def close(self):
        self.http.close()
        self.runtime.close()

    def request(self, method, path, body=None, deadline=None):
        timeout = 30 if deadline is None else max(0.01, min(30, deadline-time.monotonic()))
        response = self.http.request(method, '/api/v1'+path, json=body, timeout=timeout)
        response.raise_for_status()
        return response.json() if response.content else None

    def catalog(self):
        return self.request('GET', '/runtime/catalog')

    def install_agent(self, spec):
        return self.request('PUT', '/agents/'+spec['id'], spec)

    def execute(self, question, prompt, agent, folder):
        folder.mkdir()
        result = {'status':'runtime_failed', 'answer':'', 'input_tokens':None, 'output_tokens':None, 'cost':None}
        started = time.monotonic()
        try:
            self._start(question, prompt, agent, result, folder, started+self.timeout)
            self._wait(result, folder, started+self.timeout)
        except (httpx.HTTPError, TimeoutError, ValueError) as error:
            result['error'] = type(error).__name__
            self._cleanup(result, folder)
        result['seconds'] = round(time.monotonic()-started, 3)
        self._export(result, folder)
        save(folder/'execution.json', result)
        return result

    def _start(self, question, prompt, agent, result, folder, deadline):
        project = self.request('POST', '/projects', {'name':f'{agent}-{uuid.uuid4().hex[:12]}', 'question':question}, deadline)
        result['project_id'] = project['id']
        body = {'agent_id':agent, 'content':prompt, 'message_id':uuid.uuid4().hex}
        self._check_cancel(folder)
        save(folder/'request.json', {'project_id':project['id'], 'body':body})
        response = self.request('POST', f'/projects/{project["id"]}/sessions', body, deadline)
        result.update(session_id=response['session']['id'], turn_id=response['turn']['id'])
        save(folder/'started.json', result)

    def _wait(self, result, folder, deadline):
        while time.monotonic() < deadline:
            self._check_cancel(folder)
            detail = self.request('GET', _session_path(result), deadline=deadline)
            turn = _turn(detail, result['turn_id'])
            if turn['status'] != 'running':
                self._capture(result, folder, detail, turn)
                return
            time.sleep(min(1, max(0, deadline-time.monotonic())))
        raise TimeoutError('Per-case wall-time limit reached')

    def _capture(self, result, folder, detail, turn):
        save(folder/'detail.json', detail)
        result.update(turn_status=turn['status'], answer=turn['result_text'] or '')
        result['status'] = 'completed' if turn['status']=='completed' else 'runtime_failed'
        (folder/'answer.txt').write_text(result['answer'])

    def cancel(self, folder):
        self._cancelled.add(str(folder))
        if not (folder/'request.json').exists():
            return {'status':'cancelling','cleanup_pending':True}
        state=folder/'execution.json'
        if not state.exists():
            state=folder/'started.json'
        if state.exists():
            result=json.loads(state.read_text())
        else:
            request=json.loads((folder/'request.json').read_text())
            result={'status':'runtime_failed','project_id':request['project_id']}
        self._cleanup(result,folder)
        return result

    def _check_cancel(self, folder):
        if str(folder) in self._cancelled:
            raise TimeoutError('Execution cancelled by caller')

    def recover(self, folder):
        result = json.loads((folder/'execution.json').read_text())
        self._cleanup(result, folder)
        self._export(result, folder)
        save(folder/'execution.json', result)
        return result

    def _cleanup(self, result, folder):
        try:
            if not result.get('session_id'):
                self._reconcile(result, folder)
            if not result.get('turn_id'):
                result['cleanup_pending'] = (folder/'request.json').exists()
                return
            response = self.request('POST', _session_path(result)+f'/turns/{result["turn_id"]}/cancel')
            result.update(cleanup_pending=response['status']=='running', turn_status=response['status'])
            detail = self.request('GET', _session_path(result))
            result['answer'] = _turn(detail,result['turn_id'])['result_text'] or ''
            save(folder/'detail.json',detail)
            (folder/'answer.txt').write_text(result['answer'])
        except (httpx.HTTPError, ValueError):
            result['cleanup_pending'] = True

    def _reconcile(self, result, folder):
        if not (folder/'request.json').exists():
            return
        submitted = json.loads((folder/'request.json').read_text())
        sessions = self.request('GET', f'/projects/{submitted["project_id"]}/sessions')
        key = submitted['body']['message_id']
        matching = [s for s in sessions if any(m['id']==key for m in s['messages'])]
        if not matching:
            return
        result['session_id'] = matching[0]['id']
        detail = self.request('GET', _session_path(result))
        turns = [t for t in detail['run']['turns'] if t['message_id']==key]
        if turns:
            result['turn_id'] = turns[0]['id']
        save(folder/'started.json', result)

    def _export(self, result, folder):
        if not result.get('session_id'):
            return
        for kind, prefix in [('trajectory',''), ('title_trajectory','title-')]:
            try:
                response = self.runtime.get(f'/api/v1/runtime/sessions/{prefix}{result["session_id"]}/export')
                response.raise_for_status()
                traces = response.json()
                save(folder/f'{kind}.json', traces)
                result[kind+'_complete'] = all(t['status']!='running' for r in traces for t in r['turns'])
            except httpx.HTTPError:
                result[kind+'_missing'] = True


def _session_path(result):
    return f'/projects/{result["project_id"]}/sessions/{result["session_id"]}'


def _turn(detail, turn_id):
    return next(turn for turn in detail['run']['turns'] if turn['id']==turn_id)
