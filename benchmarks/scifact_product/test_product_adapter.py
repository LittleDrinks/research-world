import json

import httpx

from benchmarks.product_adapter import ResearchWorld


class AcceptedTimeout:
    def __init__(self, reachable=True):
        self.body=None
        self.reachable=reachable
        self.submissions=0
        self.cancelled=False

    def __call__(self, request):
        path=request.url.path
        if request.method=='POST' and path=='/api/v1/projects':
            return httpx.Response(201,json={'id':'project'})
        if request.method=='POST' and path.endswith('/sessions'):
            self.body=json.loads(request.content)
            self.submissions+=1
            raise httpx.ReadTimeout('response lost after acceptance',request=request)
        if not self.reachable:
            raise httpx.ConnectError('offline',request=request)
        return self.read(request)

    def read(self, request):
        path=request.url.path
        if path.endswith('/sessions'):
            return httpx.Response(200,json=[{'id':'session','messages':[{'id':self.body['message_id']}]}])
        if path.endswith('/cancel'):
            self.cancelled=True
            return httpx.Response(200,json={'status':'cancelled'})
        if path.endswith('/export'):
            return httpx.Response(200,json=[{'turns':[self.turn()]}])
        return httpx.Response(200,json={'run':{'turns':[self.turn()]}})

    def turn(self):
        return {'id':'turn','message_id':self.body['message_id'],
                'status':'cancelled' if self.cancelled else 'running','result_text':None}


def adapter(handler):
    return ResearchWorld('http://product','http://runtime',timeout=1,transport=httpx.MockTransport(handler))


def test_lost_acceptance_response_recovers_cancels_and_exports(tmp_path):
    server=AcceptedTimeout()
    result=adapter(server).execute('question','prompt','agent',tmp_path/'case')
    assert result['status']=='runtime_failed'
    assert result['session_id']=='session' and result['turn_id']=='turn'
    assert server.submissions==1 and server.cancelled
    assert result['cleanup_pending'] is False
    assert json.loads((tmp_path/'case/request.json').read_text())['body']==server.body
    assert (tmp_path/'case/trajectory.json').exists()


def test_offline_cleanup_remains_pending_and_can_be_recovered(tmp_path):
    server=AcceptedTimeout(reachable=False)
    product=adapter(server)
    folder=tmp_path/'case'
    result=product.execute('question','prompt','agent',folder)
    assert result['cleanup_pending'] is True and not server.cancelled
    server.reachable=True
    recovered=product.recover(folder)
    assert recovered['cleanup_pending'] is False and server.cancelled
    assert server.submissions==1
    assert recovered['status']=='runtime_failed'


def test_failed_execution_cannot_be_interpreted_as_valid_nei():
    from .protocol import interpret
    result=interpret({'status':'runtime_failed','answer':'{"id":1,"evidence":{}}'}, {'id':1})
    assert result['status']=='runtime_failed' and result['prediction']=={'id':1,'evidence':{}}


def test_complete_answer_is_not_scored_by_product_adapter(tmp_path):
    def respond(request):
        if request.url.path=='/api/v1/projects':return httpx.Response(201,json={'id':'project'})
        if request.url.path.endswith('/export'):return httpx.Response(200,json=[{'turns':[]}])
        if request.method=='POST':return httpx.Response(201,json={'session':{'id':'session'},'turn':{'id':'turn'}})
        return httpx.Response(200,json={'run':{'turns':[{'id':'turn','status':'completed','result_text':'plain research answer'}]}})
    result=adapter(respond).execute('question','prompt','agent',tmp_path/'case')
    assert result['status']=='completed' and result['answer']=='plain research answer'
    assert 'prediction' not in result
