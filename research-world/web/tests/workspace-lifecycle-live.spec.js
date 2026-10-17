import {test,expect} from '@playwright/test';

test.use({trace:'off',screenshot:'off'});
test.skip(process.env.RW_WORKSPACE_LIVE!=='1','Requires local Compose and Docker workspaces');

async function create(request){
  const response=await request.post('/api/v1/projects',{data:{name:'自动启停验收 '+Date.now(),question:'验证工作区生命周期'}});
  expect(response.status()).toBe(201);return (await response.json()).id;
}

const root=id=>'/api/v1/projects/'+encodeURIComponent(id);
async function status(request,id){return (await (await request.get(root(id)+'/workspace')).json()).status;}
async function open(page,id){
  await page.addInitScript(value=>localStorage.setItem('rw.active_project',value),id);
  await page.goto('/workspace');
  await expect(page.getByText('工作区已就绪')).toBeVisible({timeout:90000});
}
async function file(page,request,method){
  const workspace=new URL(await page.getByRole('link',{name:'打开 JupyterLab'}).getAttribute('href'),page.url());
  const token=workspace.searchParams.get('token');workspace.search='';workspace.pathname=workspace.pathname.replace(/lab$/,'api/contents/lifecycle.txt');
  const options={headers:{Authorization:'token '+token}};
  if(method==='PUT')options.data={type:'file',format:'text',content:'persistent-project-file'};
  const response=await request.fetch(workspace.href,{...options,method});
  expect(response.ok()).toBe(true);
  if(method==='GET')expect((await response.json()).content).toBe('persistent-project-file');
}
async function cleanup(request,id){
  await expect.poll(()=>status(request,id),{timeout:90000}).toBe('exited');
  expect((await request.delete(root(id))).status()).toBe(204);
}

test('real project starts, survives module and tab changes, stops on last exit and retains files',async({page,context,request})=>{
  const id=await create(request);let second;
  try{
    await open(page,id);await file(page,request,'PUT');
    await page.getByRole('link',{name:'设置',exact:true}).click();
    await page.getByRole('link',{name:'实验工作区',exact:true}).click();
    await expect(page.getByText('工作区已就绪')).toBeVisible();
    second=await context.newPage();await open(second,id);
    await page.getByRole('link',{name:'切换项目'}).click();
    expect(await status(request,id)).toBe('ready');await file(second,request,'GET');
    await second.close();await expect.poll(()=>status(request,id),{timeout:30000}).toBe('exited');
    await open(page,id);await file(page,request,'GET');
    await page.reload();await expect(page.getByText('工作区已就绪')).toBeVisible({timeout:90000});
    expect(await status(request,id)).toBe('ready');
  }finally{if(second&&!second.isClosed())await second.close();await page.close();await cleanup(request,id);}
});

test('real exit during startup leaves no running container',async({page,request})=>{
  const id=await create(request);
  try{
    await page.addInitScript(value=>localStorage.setItem('rw.active_project',value),id);
    await page.goto('/workspace');await expect(page.getByRole('status')).toBeVisible();
    await page.getByRole('link',{name:'切换项目'}).click();
    await expect.poll(()=>status(request,id),{timeout:90000}).toBe('exited');
  }finally{await page.close();await cleanup(request,id);}
});
