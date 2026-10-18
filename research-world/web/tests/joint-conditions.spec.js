import {test,expect} from '@playwright/test';

async function post(request,path,data) {
  const response=await request.post(path,{data});
  expect(response.ok(),await response.text()).toBeTruthy();
  return response.json();
}

async function seed(request) {
  const project=await post(request,'/api/v1/projects',{name:`联合条件验收 ${Date.now()}`,question:'轨道稳定性'});
  const root=`/api/v1/projects/${project.id}`;
  const artifact=await post(request,root+'/artifacts',{content:'q049 引用内容：实验和前提必须区分。',media_type:'text/plain'});
  const records=[];
  for (const title of ['守恒前提','耗散尺度','碰撞条件','目标解释']) records.push(await post(request,root+'/records',{type:'direction',content:{title,text:'待核查'},artifact_ids:[artifact.id]}));
  const conditions=[];
  for (const rule of ['AND','OR','k-of-N']) conditions.push(await post(request,root+'/joint-conditions',{
    title:`${rule} 关系示例`,rule,k:rule==='k-of-N'?2:null,members:records.slice(0,3).map(r=>({record_id:r.id,role:r.content.title})),
    target_id:records[3].id,statement:'限定条件下的解释',rationale:'不同条件分别承担解释的一部分。',evidence:[{artifact_id:artifact.id,locator:'q049 原文定位'}],
  }));
  return {root,project,records,conditions};
}

test('joint junctions, list, evidence, refresh, revocation and mobile use real API',async({page,request})=>{
  const fixture=await seed(request);
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  try {
    await page.addInitScript(id=>localStorage.setItem('rw.active_project',id),fixture.project.id);
    await page.goto('/map');
    await expect(page.locator('.joint-node')).toHaveCount(3,{timeout:90000});
    await checkJunctionAndRefresh(page,request);
    await checkListAndMobile(page);
    await checkRevocation(page,request,fixture);
    expect(errors).toEqual([]);
  } finally {
    await page.close();
    await request.post(fixture.root+'/workspace/stop');
    await request.delete(fixture.root);
  }
});

async function checkJunctionAndRefresh(page,request) {
    await page.locator('.joint-node').filter({hasText:'AND 关系示例'}).click();
    await expect(page.locator('.joint-inspector')).toContainText('全部 3 项共同满足');
    await expect(page.locator('.joint-inspector')).toContainText('不同条件分别承担解释的一部分。');
    const href=await page.getByRole('link',{name:'查看原文'}).getAttribute('href');
    expect(await (await request.get(href)).text()).toContain('q049 引用内容');
    await page.reload();
    await expect(page.locator('.joint-inspector')).toContainText('AND 关系示例');
}

async function checkListAndMobile(page) {
  await page.getByRole('button',{name:'条件列表 · 3'}).click();
  await page.locator('.joint-list-item').filter({hasText:'OR 关系示例'}).click();
  await expect(page.locator('.joint-inspector')).toContainText('至少满足其中一项');
  await page.locator('.joint-list-item').filter({hasText:'k-of-N 关系示例'}).click();
  await expect(page.locator('.joint-inspector')).toContainText('3 项中至少满足 2 项');
  await page.setViewportSize({width:390,height:844});
  await page.locator('.joint-inspector').scrollIntoViewIfNeeded();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await expect(page.locator('.joint-inspector')).toContainText('q049 原文定位');
  await page.locator('.joint-inspector .joint-record-link').first().click();
  await expect(page.locator('.inspector-header h1')).toContainText('目标解释');
  await expect(page.locator('.inspector .joint-links .joint-list-item')).toHaveCount(3);
}

async function checkRevocation(page,request,fixture) {
  expect((await request.delete(`${fixture.root}/records/${fixture.records[0].id}`)).ok()).toBeTruthy();
  await page.goto(`/map?node=${encodeURIComponent(fixture.conditions[0].id)}`);
  await expect(page.locator('.joint-inspector')).toContainText('部分研究对象已撤销');
  await expect(page.locator('.joint-inspector')).toContainText('研究对象已撤销');
  await expect(page.locator('.joint-inspector .joint-record-link').first()).toContainText('目标解释');
}
