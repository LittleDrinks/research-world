import {test,expect} from '@playwright/test';

const project='project:'+'a'.repeat(24);
const other='project:'+'b'.repeat(24);
async function fixture(page){
  const projects=[project,other].map((id,index)=>({id,name:index?'另一个项目':'自动工作区',question:'生命周期',created_at:'2026-01-01',node_count:0}));
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:new URL(r.request().url()).searchParams.get('project_id')||project,projects,sessions:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  const connections=[];
  await page.routeWebSocket('**/workspace/presence',socket=>{
    const entry={socket,closed:false};connections.push(entry);
    socket.onClose(()=>{entry.closed=true;});socket.send(JSON.stringify({status:'starting'}));
  });
  return connections;
}

const ready=socket=>socket.send(JSON.stringify({status:'ready',url:'/lab?token=synthetic-test'}));

test('enter starts, modules retain connection, exit closes it',async({page})=>{
  const connections=await fixture(page);
  await page.goto('/projects');
  await expect(page.locator('.project-open').first()).toBeVisible();expect(connections).toHaveLength(0);
  await page.locator('.project-open').first().click();
  await expect(page.getByRole('status')).toHaveText('正在准备文件和运行环境，首次启动可能需要一点时间…');
  expect(connections).toHaveLength(1);ready(connections[0].socket);
  await page.getByRole('link',{name:'实验工作区',exact:true}).click();
  await expect(page.getByText('工作区已就绪')).toBeVisible();
  await expect(page.getByRole('button',{name:'启动工作区'})).toHaveCount(0);
  await page.getByRole('link',{name:'设置',exact:true}).click();
  await page.getByRole('link',{name:'实验工作区',exact:true}).click();
  expect(connections).toHaveLength(1);expect(connections[0].closed).toBe(false);
  await page.getByRole('link',{name:'切换项目'}).click();
  await expect.poll(()=>connections[0].closed).toBe(true);
});

test('switching projects closes the old connection and starts the selected project',async({page})=>{
  const connections=await fixture(page);await page.goto('/workspace');
  await expect.poll(()=>connections.length).toBe(1);ready(connections[0].socket);
  await expect(page.getByText('工作区已就绪')).toBeVisible();
  await page.getByRole('link',{name:'切换项目'}).click();
  await page.locator('.project-open').filter({hasText:'另一个项目'}).click();
  await expect.poll(()=>connections.length).toBe(2);
  expect(connections[0].closed).toBe(true);
  expect(decodeURIComponent(connections[1].socket.url())).toContain(other);
  ready(connections[1].socket);
  await page.getByRole('link',{name:'实验工作区',exact:true}).click();
  await expect(page.locator('.workspace-page header')).toContainText('另一个项目');
});

test('startup failure supports retry and exit during startup',async({page})=>{
  const connections=await fixture(page);await page.goto('/workspace');
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
  const connections=await fixture(page);await page.goto('/workspace');
  await expect.poll(()=>connections.length).toBe(1);ready(connections[0].socket);
  await expect(page.getByText('工作区已就绪')).toBeVisible();connections[0].socket.close();
  await expect(page.getByRole('alert')).toHaveText('工作区连接已断开，请重试');
  await page.getByRole('button',{name:'重试',exact:true}).click();
  await expect.poll(()=>connections.length).toBe(2);ready(connections[1].socket);
  await expect(page.getByText('工作区已就绪')).toBeVisible();
});
