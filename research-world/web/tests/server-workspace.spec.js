import {test,expect} from '@playwright/test';

test.use({trace:'off',screenshot:'off'});
test('server gateway opens project files and carries authenticated terminal and kernel sockets',async({page,request})=>{
  test.skip(process.env.RW_SERVER_TEST!=='1','Requires server Compose overlay');
  const project=await createProject(request,'服务器入口验收');
  const root=`/api/v1/projects/${project.id}`;
  try{
    const started=await request.post(root+'/workspace');expect(started.ok()).toBeTruthy();
    const state=await started.json();expect(state.status).toBe('ready');expect(state.url.startsWith('/labs/')).toBeTruthy();
    const apiPath=new URL(state.url,'http://gateway').pathname.replace(/lab$/,'api/contents');
    expect([302,403]).toContain((await request.get(apiPath,{maxRedirects:0})).status());
    await page.goto('/projects');
    await exerciseWorkspace(page,state.url);
    await page.goto(`/workspace/server-check.py?project=${project.id}`);
    await expect(page.locator('.jp-CodeMirrorEditor').first()).toContainText('print(42)',{timeout:30000});
    expect((await request.get('/labs/'+'f'.repeat(24)+'/lab',{headers:{'X-Workspace-Upstream':'127.0.0.1:8098'}})).status()).toBe(404);
  }finally{await request.post(root+'/workspace/stop');await request.delete(root);}
});

async function exerciseWorkspace(page,workspaceUrl){
  const result=await page.evaluate(async path=>{
    const url=new URL(path,location.origin),base=url.pathname.replace(/lab$/,''),token=url.searchParams.get('token');
    const api=async(endpoint,method='GET',body)=>{
      const response=await fetch(base+'api/'+endpoint,{method,headers:{Authorization:'token '+token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
      if(!response.ok)throw Error('Jupyter API failed: '+response.status);
      return response.status===204?null:response.json();
    };
    await api('contents/server-check.py','PUT',{type:'file',format:'text',content:'print(42)\n'});
    const terminal=await api('terminals','POST',{}),kernel=await api('kernels','POST',{name:'python3'});
    const terminalResult=await window.runWorkspaceSocket(base+`terminals/websocket/${terminal.name}`,token,'terminal');
    const kernelResult=await window.runWorkspaceSocket(base+`api/kernels/${kernel.id}/channels`,token,'kernel');
    await api('terminals/'+terminal.name,'DELETE');await api('kernels/'+kernel.id,'DELETE');
    return {terminalResult,kernelResult};
  },workspaceUrl);
  expect(result).toEqual({terminalResult:true,kernelResult:true});
}

test.beforeEach(async({page})=>{
  await page.addInitScript(()=>{
    window.runWorkspaceSocket=(path,token,kind)=>new Promise((resolve,reject)=>{
      const url=new URL(path,location.origin);url.protocol=location.protocol==='https:'?'wss:':'ws:';url.searchParams.set('token',token);
      const session=crypto.getRandomValues(new Uint32Array(4)).join('-');url.searchParams.set('session_id',session);
      const ws=new WebSocket(url),timer=setTimeout(()=>{ws.close();reject(Error('Workspace socket timed out'));},20000);
      const finish=()=>{clearTimeout(timer);ws.close();resolve(true);};
      ws.onerror=()=>{clearTimeout(timer);reject(Error('Workspace socket failed'));};
      ws.onopen=()=>ws.send(JSON.stringify(kind==='terminal'?['stdin','printf "GATEWAY_%s\\n" "TERMINAL_OK"\n']:{header:{msg_id:session+'-execute',username:'test',session,msg_type:'execute_request',version:'5.3'},parent_header:{},metadata:{},channel:'shell',content:{code:'print("GATEWAY_KERNEL_OK")',silent:false,store_history:false,user_expressions:{},allow_stdin:false,stop_on_error:true}}));
      ws.onmessage=event=>{const value=JSON.parse(event.data);if(kind==='terminal'?value[0]==='stdout'&&value[1].includes('GATEWAY_TERMINAL_OK'):value.msg_type==='stream'&&value.content.text.includes('GATEWAY_KERNEL_OK'))finish();};
    });
  });
});


for(const existing of [false,true])test(`browser without secure-context UUID sends ${existing?'existing':'new'} messages`,async({page,request})=>{
  test.skip(process.env.RW_SERVER_TEST!=='1','Requires server Compose overlay');
  const project=await createProject(request,'HTTP发送验收');
  try{
    await page.addInitScript(id=>localStorage.setItem('rw.active_project',id),project.id);
    await page.route('**/sessions/s-http',r=>r.fulfill({json:{session:{id:'s-http',project_id:project.id,title:'HTTP',messages:[]},run:{turns:[]}}}));
    let message;
    await page.route('**/sessions**',r=>{if(r.request().method()!=='POST')return r.fallback();message=r.request().postDataJSON();return r.fulfill({status:400,json:{detail:'测试请求已接收'}});});
    await page.addInitScript(()=>Object.defineProperty(crypto,'randomUUID',{value:undefined}));
    await page.goto(existing?'/chat/s-http':'/chat');
    await expect(page.getByLabel('研究消息')).toBeVisible({timeout:90000});
    await page.getByLabel('研究消息').fill('验证普通HTTP发送');await page.getByLabel('研究消息').press('Control+Enter');
    await expect.poll(()=>message?.message_id).toMatch(/^\S+$/);
  }finally{await request.delete('/api/v1/projects/'+project.id);}
});

async function createProject(request,name){
  const response=await request.post('/api/v1/projects',{data:{name:name+' '+Date.now(),question:'验证远程工作区'}});
  expect(response.status()).toBe(201);
  return response.json();
}
