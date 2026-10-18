import {test,expect} from '@playwright/test';

const project='project:'+'a'.repeat(24);
const other='project:'+'b'.repeat(24);
async function fixture(page){
  const projects=[project,other].map((id,index)=>({id,name:index?'另一个项目':'自动工作区',question:'生命周期',created_at:'2026-01-01',node_count:0}));
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:new URL(r.request().url()).searchParams.get('project_id')||project,projects,sessions:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  await page.route('**/local-map',r=>r.fulfill({json:{records:[],relations:[],artifacts:[]}}));
  await page.context().route('**/lab?*',r=>r.fulfill({contentType:'text/html',body:'<h1>JupyterLab</h1>'}));
  const connections=[];
  await page.routeWebSocket('**/workspace/presence',socket=>{
    const entry={socket,closed:false};connections.push(entry);
    socket.onClose(()=>{entry.closed=true;});socket.send(JSON.stringify({status:'starting'}));
  });
  return connections;
}

const link=page=>page.getByRole('link',{name:'实验工作区',exact:true});
const ready=(socket,url='/lab?token=synthetic-test')=>socket.send(JSON.stringify({status:'ready',url}));
const usable=page=>expect(link(page)).toHaveAttribute('aria-disabled','false');

async function openLab(page){
  const popup=page.waitForEvent('popup');await link(page).click();const lab=await popup;
  await expect(lab.getByRole('heading',{name:'JupyterLab'})).toBeVisible();await lab.close();
  await expect(page).toHaveURL(/\/map$/);
}

test('enter starts, modules retain connection, exit closes it',async({page})=>{
  const connections=await fixture(page);
  await page.goto('/projects');
  await expect(page.locator('.project-open').first()).toBeVisible();expect(connections).toHaveLength(0);
  await page.locator('.project-open').first().click();
  await expect(page.getByRole('status')).toHaveText('正在准备文件和运行环境，首次启动可能需要一点时间…');
  await expect(link(page)).toHaveAttribute('aria-disabled','true');await expect(link(page)).not.toHaveAttribute('href');
  expect(connections).toHaveLength(1);ready(connections[0].socket);await usable(page);
  await expect(link(page).locator('.workspace-external')).toBeVisible();await openLab(page);
  await expect(page.getByRole('link',{name:'打开 JupyterLab'})).toHaveCount(0);
  await page.getByRole('link',{name:'设置',exact:true}).click();
  await page.getByRole('link',{name:'地图',exact:true}).click();
  expect(connections).toHaveLength(1);expect(connections[0].closed).toBe(false);
  await page.getByRole('link',{name:'切换项目'}).click();
  await expect.poll(()=>connections[0].closed).toBe(true);
});

test('switching projects closes the old connection and starts the selected project',async({page})=>{
  const connections=await fixture(page);await page.goto('/map');
  await expect.poll(()=>connections.length).toBe(1);ready(connections[0].socket);
  await usable(page);
  await page.getByRole('link',{name:'切换项目'}).click();
  await page.locator('.project-open').filter({hasText:'另一个项目'}).click();
  await expect.poll(()=>connections.length).toBe(2);
  expect(connections[0].closed).toBe(true);
  expect(decodeURIComponent(connections[1].socket.url())).toContain(other);
  ready(connections[1].socket,'/lab?project=other');
  await expect(link(page)).toHaveAttribute('href','/lab?project=other');
});

test('startup failure supports retry and exit during startup',async({page})=>{
  const connections=await fixture(page);await page.goto('/map');
  await expect.poll(()=>connections.length).toBe(1);
  connections[0].socket.send(JSON.stringify({status:'error',detail:'工作区启动失败，请重试'}));
  await expect(page.getByRole('alert')).toHaveText('工作区启动失败，请重试');
  await page.getByRole('button',{name:'重试',exact:true}).click();
  await expect.poll(()=>connections.length).toBe(2);
  expect(connections[0].closed).toBe(true);
  await expect(page.getByRole('status')).toBeVisible();
  await page.getByRole('link',{name:'切换项目'}).click();
  await expect.poll(()=>connections[1].closed).toBe(true);
});

test('connection loss exposes retry instead of stale ready state',async({page})=>{
  const connections=await fixture(page);await page.goto('/map');
  await expect.poll(()=>connections.length).toBe(1);ready(connections[0].socket);
  await usable(page);connections[0].socket.close();
  await expect(page.getByRole('alert')).toHaveText('工作区连接已断开，请重试');
  await expect(link(page)).not.toHaveAttribute('href');
  await page.getByRole('button',{name:'重试',exact:true}).click();
  await expect.poll(()=>connections.length).toBe(2);ready(connections[1].socket);
  await usable(page);
});


test('mobile navigation opens JupyterLab and closes the menu without leaving the project',async({page})=>{
  await page.setViewportSize({width:390,height:844});const connections=await fixture(page);
  await page.goto('/map');await expect.poll(()=>connections.length).toBe(1);ready(connections[0].socket);
  await page.getByRole('button',{name:'打开导航'}).click();await usable(page);
  await expect(link(page).locator('.workspace-external')).toBeVisible();await openLab(page);
  await expect(page.locator('.sidebar')).not.toHaveClass(/sidebar-open/);
  expect(connections[0].closed).toBe(false);
});
