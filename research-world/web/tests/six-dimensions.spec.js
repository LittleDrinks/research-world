import {test,expect} from '@playwright/test';

test('six dimensions show evidence, corrections, applicability and execution separately',async({page,request})=>{
  const created=await request.post('/api/v1/projects',{data:{name:`rubric-browser-${Date.now()}`,question:'Check fixed evidence'}});
  expect(created.ok(),await created.text()).toBeTruthy();
  const project=await created.json();
  const root=`/api/v1/projects/${project.id}`;
  try{
    const {report,record}=await publish(request,root);
    await page.goto(report.view_url);await verifyDimensions(page,request);
    await page.setViewportSize({width:390,height:844});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    await page.goto(`/projects/${encodeURIComponent(project.id)}/records/${encodeURIComponent(record.id)}`);
    await expect(page.locator('.dimension-item')).toHaveCount(6);
  }finally{await page.close();expect((await request.post(root+'/workspace/stop')).ok()).toBeTruthy();expect((await request.delete(root)).status()).toBe(204);}
});

async function publish(request,root){
  const original=await (await request.post(root+'/artifacts',{data:{content:'Measured error: 0.2',media_type:'text/plain'}})).json();
  const record=await (await request.post(root+'/records',{data:{type:'experiment',content:{title:'步长比较'},artifact_ids:[original.id]}})).json();
  const template=(await (await request.get(root+'/artifact-templates')).json())[0];
  const data={...template.example,title:'步长检查六维评价',target_artifact_id:original.id};
  data.dimensions[0]={...data.dimensions[0],result:'scored',score:1,reason:'范围缺少积分时长。',improvement:'明确积分周期数。',evidence:[{artifact_id:original.id,locator:'误差输出第1行'}]};
  data.dimensions[2]={...data.dimensions[2],action:'skip',result:'not_applicable',reason:'本次只复核一个计算，不比较研究方向。',improvement:''};
  data.conclusion.verdict='revise';
  const response=await request.post(root+'/artifacts',{data:{schema_id:template.id,record_id:record.id,content:JSON.stringify(data)}});
  expect(response.status(),await response.text()).toBe(201);
  return {report:await response.json(),record};
}

async function verifyDimensions(page,request){
  await expect(page.locator('.dimension-item')).toHaveCount(6);
  await expect(page.getByRole('region',{name:'六维评价'})).toContainText('已评 1 / 6 维');
  await expect(page.locator('.execution-evidence')).toContainText('执行未核验');
  await expect(page.locator('.dimension-item').nth(2)).toContainText('不适用');
  await expect(page.getByText('明确积分周期数。')).toBeVisible();
  await page.locator('.dimension-item').first().getByText('评分判据').click();
  await expect(page.locator('.dimension-item').first().locator('ol li')).toHaveCount(3);
  const evidence=page.getByRole('link',{name:'证据 1 · 误差输出第1行'});
  expect((await request.get(await evidence.getAttribute('href'))).ok()).toBeTruthy();
  const exported=await request.get(await page.getByText('导出 Markdown').getAttribute('href'));
  expect(await exported.text()).toContain('方向质量 · 不适用');
}
