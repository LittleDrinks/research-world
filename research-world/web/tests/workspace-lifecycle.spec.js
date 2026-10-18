import {test,expect} from '@playwright/test';

const project='project:'+'a'.repeat(24),other='project:'+'b'.repeat(24);
const link=page=>page.getByRole('link',{name:'实验工作区',exact:true});
const usable=page=>expect(link(page)).toHaveAttribute('aria-disabled','false');

async function fixture(page){
  const state={value:{status:'ready',url:'/lab?project=first'},starts:[],stops:[],statusError:false,stopError:false};
  const projects=[project,other].map((id,index)=>({id,name:index?'另一个项目':'自动工作区',question:'生命周期',created_at:'2026-01-01',node_count:0}));
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:new URL(r.request().url()).searchParams.get('project_id')||project,projects,sessions:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  await page.route('**/local-map',r=>r.fulfill({json:{records:[],relations:[],artifacts:[],joint_conditions:[]}}));
  await page.context().route('**/lab?*',r=>r.fulfill({contentType:'text/html',body:'<h1>JupyterLab</h1>'}));
  await workspaceRoutes(page,state);
  return state;
}

async function workspaceRoutes(page,state){
  await page.route('**/api/v1/projects/*/workspace',async r=>{
    if(r.request().method()==='POST'){
      state.starts.push(r.request().url());if(state.start)await state.start();
      state.value={status:'ready',url:'/lab?project=first'};
    }
    return r.fulfill({json:state.value});
  });
  await page.route('**/api/v1/workspaces',r=>state.statusError?r.fulfill({status:503,json:{detail:'unavailable'}}):r.fulfill({json:{[project]:state.value.status,[other]:'not_started'}}));
  await page.route('**/workspace/stop',async r=>{
    state.stops.push(r.request().url());if(state.stop)await state.stop();
    if(state.stopError)return r.fulfill({status:503,json:{detail:'停止失败，请重试'}});
    state.value={status:'exited'};return r.fulfill({json:state.value});
  });
}

async function openLab(page){
  const popup=page.waitForEvent('popup');await link(page).click();const lab=await popup;
  await expect(lab.getByRole('heading',{name:'JupyterLab'})).toBeVisible();await lab.close();
  await expect(page).toHaveURL(/\/map$/);
}

test('ready workspace refresh and navigation never start or stop it',async({page})=>{
  const state=await fixture(page);await page.goto('/map');await usable(page);
  await expect(link(page).locator('.workspace-external')).toBeVisible();await openLab(page);
  await page.reload();await usable(page);
  await page.getByRole('link',{name:'设置',exact:true}).click();
  await page.getByRole('link',{name:'地图',exact:true}).click();
  await page.getByRole('link',{name:'切换项目'}).click();
  await expect(page.locator('.project-row').first()).toContainText('运行中');
  expect(state.starts).toEqual([]);expect(state.stops).toEqual([]);
});

test('startup continues after leaving and is visible in project list',async({page})=>{
  const state=await fixture(page);state.value={status:'not_started'};let finish;
  state.start=()=>new Promise(resolve=>{finish=resolve;});
  await page.goto('/map');await expect.poll(()=>state.starts.length).toBe(1);
  await expect(link(page)).not.toHaveAttribute('href');
  await page.getByRole('link',{name:'切换项目'}).click();finish();
  await expect(page.locator('.project-row').first()).toContainText('运行中');
  expect(state.stops).toEqual([]);
});

test('manual stop has pending feedback, retries failure and keeps project list open',async({page})=>{
  const state=await fixture(page);state.stopError=true;let finish;
  state.stop=()=>new Promise(resolve=>{finish=resolve;});
  await page.goto('/projects');const stop=page.getByRole('button',{name:'停止 自动工作区 工作区'});
  await stop.click();await expect(stop).toBeDisabled();finish();
  await expect(page.getByRole('alert')).toHaveText('停止失败，请重试');
  await expect(page.locator('.project-row').first()).toContainText('运行中');
  state.stop=null;state.stopError=false;await stop.click();
  await expect(page.locator('.project-row').first()).toContainText('已停止');
  await expect(page.locator('.project-row').last()).toContainText('未启动');
  await expect(page).toHaveURL(/\/projects$/);expect(state.starts).toEqual([]);
});

test('state lookup failure never reports stopped projects',async({page})=>{
  const state=await fixture(page);state.statusError=true;await page.goto('/projects');
  await expect(page.getByRole('alert')).toHaveText('工作区状态暂不可用');
  await expect(page.locator('.workspace-state')).toHaveText(['状态不可用','状态不可用']);
  expect(state.starts).toEqual([]);expect(state.stops).toEqual([]);
});

test('another tab stopping clears the link and never restarts until requested',async({page})=>{
  const state=await fixture(page);await page.goto('/map');await usable(page);
  state.value={status:'exited'};
  await expect(page.getByRole('heading',{name:'工作区已停止'})).toBeVisible();
  await expect(link(page)).not.toHaveAttribute('href');expect(state.starts).toEqual([]);
  await page.getByRole('button',{name:'重新启动'}).click();await usable(page);
  expect(state.starts).toHaveLength(1);
});

test('switching projects uses the selected workspace URL',async({page})=>{
  const state=await fixture(page);await page.goto('/map');await usable(page);
  await page.getByRole('link',{name:'切换项目'}).click();
  state.value={status:'ready',url:'/lab?project=other'};
  await page.locator('.project-open').filter({hasText:'另一个项目'}).click();
  await expect(link(page)).toHaveAttribute('href','/lab?project=other');expect(state.stops).toEqual([]);
});

test('mobile navigation opens lab and project list exposes stop',async({page})=>{
  await page.setViewportSize({width:390,height:844});await fixture(page);await page.goto('/map');
  await page.getByRole('button',{name:'打开导航'}).click();await usable(page);await openLab(page);
  await expect(page.locator('.sidebar')).not.toHaveClass(/sidebar-open/);
  await page.goto('/projects');await expect(page.getByRole('button',{name:'停止 自动工作区 工作区'})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
});
