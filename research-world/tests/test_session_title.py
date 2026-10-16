import asyncio
from types import SimpleNamespace
import pytest

from server.kernel_interface import create_kernel
from server.session_title import _title


class TitleRuntime:
    async def launch(self,spec,session_id):
        self.spec=spec
    async def submit(self,session_id,message):
        self.message=message
        return SimpleNamespace(id='title-turn')
    async def subscribe(self,turn):
        yield {'type':'turn_end','data':{'status':'completed','result_text':'{"title":"行星轨道稳定性"}'}}


@pytest.mark.asyncio
async def test_title_agent_has_only_first_message_and_no_tools(tmp_path):
    kernel=create_kernel(tmp_path/'graph.db',tmp_path/'artifacts')
    project=kernel.create_project('Orbit','Question')
    session=kernel.create_session(project.id,'session','first message')
    runtime=TitleRuntime()
    await _title(kernel,runtime,project.id,session.id,{'model':'test','tools':['graph'],'skills':['research-report']},'Why stable?',asyncio.Lock())
    assert runtime.spec['tools']==runtime.spec['skills']==[]
    assert runtime.spec['thinking']=='off'
    assert 'message_to_summarize' in runtime.message['content']
    assert runtime.spec['params']=={'mode':'title'}
    assert kernel.get_session(project.id,session.id).title=='行星轨道稳定性'
    assert kernel.get_session(project.id,session.id).messages==()


def test_task_refusal_is_not_accepted_as_title(tmp_path):
    from server.session_title import _save_title
    kernel=create_kernel(tmp_path/'graph.db',tmp_path/'artifacts')
    project=kernel.create_project('Orbit','Question')
    kernel.create_session(project.id,'session','first message')
    _save_title(kernel,project.id,'session',{'status':'completed','result_text':'我没有可用的 record 工具，无法执行任务。'})
    assert kernel.get_session(project.id,'session').title=='first message'
