import {test,expect} from '@playwright/test';

async function createProject(page,name){
  await page.goto('/projects');
  await page.getByRole('button',{name:'新建项目',exact:true}).first().click();
  await page.getByLabel('名称').fill(name);
  await page.getByLabel('研究问题').fill('如何验证轨道长期稳定性？');
  await page.getByRole('button',{name:'创建项目',exact:true}).click();
  await expect(page).toHaveURL(/\/map/);
}

test('project creation, graph roundtrip, export and Agent settings use the real API',async({page,request})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await createProject(page,`浏览器验收 ${Date.now()}`);
  const project=await page.evaluate(()=>localStorage.getItem('rw.active_project'));
  const root=`/api/v1/projects/${encodeURIComponent(project)}`;
  const response=await request.post(root+'/records',{data:{type:'direction',content:{title:'时间步长收敛',text:'待执行计划：比较数值误差。'}}});
  expect(response.status()).toBe(201);
  await expect(page.getByText('时间步长收敛').first()).toBeVisible();
  await page.reload();
  await expect(page.getByText('时间步长收敛').first()).toBeVisible();
  await page.getByRole('link',{name:'Agent',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Agent · Pi'})).toBeVisible();
  await expect(page.getByLabel('指令')).toContainText('科学问题');
  await saveCopiedAgent(page);
  expect((await request.get(root+'/export')).status()).toBe(200);
  expect(errors).toEqual([]);
});

test('real Pi reply writes a research direction and survives refresh',async({page})=>{
  test.skip(process.env.RW_REAL_MODEL!=='1','Requires configured Pi model');
  await createProject(page,`Pi 浏览器真实闭环 ${Date.now()}`);
  await page.getByRole('link',{name:'对话',exact:true}).click();
  await page.getByRole('button',{name:'新建对话',exact:true}).click();
  await expect(page).toHaveURL(/\/chat\/s-/);
  await page.getByLabel('研究消息').fill('只调用一次 record 保存 direction，title 为“浏览器闭环方向”，text 为“待执行计划：比较两种积分时间步长的能量误差”。完成后只回复“浏览器闭环已完成”。');
  await page.getByRole('button',{name:'发送',exact:true}).click();
  await expect(page.locator('.pi-messages article').last().getByText('浏览器闭环已完成',{exact:true})).toBeVisible({timeout:150000});
  await page.reload();
  await expect(page.locator('.pi-messages article').last().getByText('浏览器闭环已完成',{exact:true})).toBeVisible();
  await page.getByRole('link',{name:'地图',exact:true}).click();
  await expect(page.getByText('浏览器闭环方向').first()).toBeVisible();
});

async function saveCopiedAgent(page) {
  await page.getByRole('button',{name:'复制为新 Agent'}).click();
  const name=`浏览器配置验收 ${Date.now()}`;
  await page.getByLabel('名称',{exact:true}).fill(name);
  await page.getByRole('button',{name:'保存 Agent',exact:true}).click();
  await expect(page.getByRole('option',{name,exact:true})).toHaveCount(1);
  await page.reload();
  await page.getByLabel('选择 Agent').selectOption({label:name});
  await expect(page.getByLabel('名称',{exact:true})).toHaveValue(name);
}
