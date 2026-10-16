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
        yield {'type':'turn_end','data':{'status':'completed','result_text':'行星轨道稳定性'}}


@pytest.mark.asyncio
async def test_title_agent_has_only_first_message_and_no_tools(tmp_path):
    kernel=create_kernel(tmp_path/'graph.db',tmp_path/'artifacts')
    project=kernel.create_project('Orbit','Question')
    session=kernel.create_session(project.id,'session','first message')
    runtime=TitleRuntime()
    await _title(kernel,runtime,project.id,session.id,{'model':'test','tools':['graph'],'skills':['research-report']},'Why stable?')
    assert runtime.spec['tools']==runtime.spec['skills']==[]
    assert runtime.spec['thinking']=='off'
    assert runtime.message['content']=='Why stable?'
    assert kernel.get_session(project.id,session.id).title=='行星轨道稳定性'
    assert kernel.get_session(project.id,session.id).messages==()
