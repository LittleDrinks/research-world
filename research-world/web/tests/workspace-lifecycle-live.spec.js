import {test,expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';

test.use({trace:'off',screenshot:'off'});
test.skip(process.env.RW_WORKSPACE_LIVE!=='1','Requires Compose and Docker workspaces');
const root=id=>'/api/v1/projects/'+encodeURIComponent(id);
const link=page=>page.getByRole('link',{name:'实验工作区',exact:true});
const ready=page=>expect(link(page)).toHaveAttribute('aria-disabled','false',{timeout:90000});
async function status(request,id){return (await (await request.get(root(id)+'/workspace')).json()).status;}

function docker(args){
  if(!process.env.RW_TEST_SSH)return execFileSync('docker',args,{encoding:'utf8'}).trim();
  const quote=value=>"'"+value.replaceAll("'","'\\''")+"'";
  return execFileSync('ssh',['-o','BatchMode=yes',process.env.RW_TEST_SSH,['docker',...args].map(quote).join(' ')],{encoding:'utf8'}).trim();
}
const container=id=>'research-world-lab-'+createHash('sha256').update(id).digest('hex').slice(0,24);
const identity=id=>docker(['inspect','--format','{{.Id}}|{{.State.StartedAt}}',container(id)]);
function background(id,start=false){
  const command=start?"import subprocess,pathlib; p=subprocess.Popen(['sleep','600'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); pathlib.Path('/workspace/lifecycle.pid').write_text(str(p.pid))":"import os,pathlib; os.kill(int(pathlib.Path('/workspace/lifecycle.pid').read_text()),0)";
  docker(['exec',container(id),'python','-c',command]);
}
async function create(request){
  const response=await request.post('/api/v1/projects',{data:{name:'持续工作区验收 '+Date.now(),question:'验证工作区保持运行'}});
  expect(response.status()).toBe(201);return (await response.json()).id;
}
async function open(page,id){
  await page.addInitScript(value=>localStorage.setItem('rw.active_project',value),id);
  await page.goto('/map');await ready(page);
}
async function file(page,request,method){
  const workspace=new URL(await link(page).getAttribute('href'),page.url());
  const token=workspace.searchParams.get('token');workspace.search='';workspace.pathname=workspace.pathname.replace(/lab$/,'api/contents/lifecycle.txt');
  const options={headers:{Authorization:'token '+token}};
  if(method==='PUT')options.data={type:'file',format:'text',content:'persistent-project-file'};
  const response=await request.fetch(workspace.href,{...options,method});expect(response.ok()).toBe(true);
  if(method==='GET')expect((await response.json()).content).toBe('persistent-project-file');
}
async function cleanup(request,id){
  expect((await request.post(root(id)+'/workspace/stop')).ok()).toBe(true);
  expect((await request.delete(root(id))).status()).toBe(204);
}
async function stopInList(page,id){
  await page.goto('/projects');
  const projects=await (await page.request.get('/api/v1/bootstrap')).json();
  const name=projects.projects.find(p=>p.id===id).name;
  const row=page.locator('.project-row').filter({has:page.getByText(name,{exact:true})});
  await expect(row.getByRole('status')).toHaveText('运行中',{timeout:90000});
  await row.getByRole('button',{name:`停止 ${name} 工作区`}).click();
  await expect(row.getByRole('status')).toHaveText('已停止',{timeout:30000});
}

test('refresh, exit and closing all tabs preserve container identity and background process until manual stop',async({page,context,request})=>{
  const id=await create(request);let reopened;
  try{
    await open(page,id);await file(page,request,'PUT');background(id,true);const original=identity(id);
    for(let i=0;i<2;i++){await page.reload();await ready(page);expect(identity(id)).toBe(original);background(id);}
    await page.goto('/projects');expect(await status(request,id)).toBe('ready');background(id);
    await page.close();expect(identity(id)).toBe(original);background(id);
    reopened=await context.newPage();await open(reopened,id);await file(reopened,request,'GET');
    expect(identity(id)).toBe(original);await openLab(reopened);
    await stopInList(reopened,id);expect(await status(request,id)).toBe('exited');
    await open(reopened,id);await file(reopened,request,'GET');
  }finally{if(reopened)await reopened.close();if(!page.isClosed())await page.close();await cleanup(request,id);}
});

test('manual stop from another tab stays stopped until explicit restart',async({page,context,request})=>{
  const id=await create(request),other=await create(request);const list=await context.newPage();
  try{
    await open(page,id);await list.goto('/projects');
    expect((await request.post(root(other)+'/workspace')).ok()).toBe(true);
    await stopInList(list,id);
    await expect(page.getByRole('heading',{name:'工作区已停止'})).toBeVisible();
    await expect(link(page)).not.toHaveAttribute('href');
    expect(await status(request,other)).toBe('ready');
    await page.getByRole('button',{name:'重新启动'}).click();await ready(page);
  }finally{await page.close();await list.close();await cleanup(request,id);await cleanup(request,other);}
});

test('exit during startup retains workspace and allows manual stop from list',async({page,request})=>{
  const id=await create(request);
  try{
    await page.addInitScript(value=>localStorage.setItem('rw.active_project',value),id);
    const starting=page.waitForRequest(r=>r.method()==='POST'&&r.url().endsWith('/workspace'));
    await page.goto('/map');await starting;await page.getByRole('link',{name:'切换项目'}).click();
    await expect.poll(()=>status(request,id),{timeout:90000}).toBe('ready');
    await stopInList(page,id);
  }finally{await page.close();await cleanup(request,id);}
});

async function openLab(page){
  const popup=page.waitForEvent('popup');await link(page).click();const lab=await popup;
  try{await expect(lab.locator('.jp-LabShell')).toBeVisible({timeout:60000});}
  finally{await lab.close();}
  await expect(page).toHaveURL(/\/map$/);
}
