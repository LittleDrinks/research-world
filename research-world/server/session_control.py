from __future__ import annotations

import secrets
from pathlib import Path


class SessionControl:
    def __init__(self, kernel, runtime, profiles, workspace):
        self.kernel, self.runtime, self.profiles = kernel, runtime, profiles
        self.workspace = Path(workspace)

    async def create(self, project_id, title, agent_id):
        project = self.kernel.get_project(project_id)
        catalog = await self.runtime.catalog()
        agent = self.profiles.get(agent_id, catalog['default_model'])
        prepared = await self.runtime.validate(agent)
        agent = {**agent, "instructions": prepared["instructions"]}
        workspace = self.workspace / project_id
        workspace.mkdir(parents=True, exist_ok=True)
        spec = _snapshot(agent, project, workspace)
        session_id = 's-' + secrets.token_hex(16)
        await self.runtime.launch(spec, session_id)
        return self.kernel.create_session(project_id, session_id, title or agent['name'])

    async def detail(self, project_id, session_id):
        session = self.kernel.get_session(project_id, session_id)
        view = await self.runtime.inspect(session_id)
        for turn in view['turns']:
            if turn['status'] in {'completed', 'limit'} and turn['result_text'] is not None:
                self.kernel.project_assistant_response(project_id, session_id, turn['message_id'], turn['result_text'])
        return {'session': self.kernel.get_session(project_id, session_id), 'run': _public_run(view)}

    async def submit(self, project_id, session_id, content, message_id=None):
        message = self.kernel.append_user_message(project_id, session_id, content, message_id)
        turn = await self.runtime.submit(session_id, {'id': message.id, 'content': content})
        return {'message': message, 'turn': turn}

    async def require_turn(self, project_id, session_id, turn_id):
        self.kernel.get_session(project_id, session_id)
        view = await self.runtime.inspect(session_id)
        if turn_id not in {t['id'] for t in view['turns']}:
            raise PermissionError('Turn belongs to another Session')

    async def events(self, project_id, session_id, turn_id, cursor):
        async for event in self.runtime.subscribe(turn_id, cursor):
            yield event
        await self.detail(project_id, session_id)


def _snapshot(agent, project, workspace):
    return {k:v for k,v in agent.items() if k != 'name'} | {
        'adapter':'pi', 'workspace':str(workspace), 'project_id':project.id,
        'instructions': agent['instructions'] + f'\n研究问题：{project.question}',
    }


def _public_run(view):
    spec = {k:v for k,v in view['agent_snapshot'].items() if k not in {'workspace','project_id'}}
    return {**view, 'agent_snapshot':spec}
