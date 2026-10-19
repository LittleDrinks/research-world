import {test,expect} from '@playwright/test';

async function post(request,path,data){
  const response=await request.post(path,{data});
  expect(response.ok(),await response.text()).toBeTruthy();
  return response.json();
}

async function seed(request){
  const project=await post(request,'/api/v1/projects',{name:`报告验收 ${Date.now()}-${Math.random()}`,question:'范围明确的研究'});
  const root=`/api/v1/projects/${project.id}`;
  const original=await post(request,root+'/artifacts',{content:'## 原始依据\n**范围：**孤立模型。\n\n\\[\nP=196.29\\,W\n\\]\n\n<script>window.reportExecuted=true</script>'});
  const record=await post(request,root+'/records',{type:'experiment',content:{title:'历史计算',text:'限定条件下的计算',attachments:[{id:original.id,name:'原文.md'}]},artifact_ids:[original.id]});
  const template=(await (await request.get(root+'/artifact-templates')).json())[0];
  const data={...template.example,title:'q049 审计阅读验收',target_artifact_id:original.id,summary:'**检查范围：**本次整理历史证据。\\(P=196.29\\,W\\)'};
  data.sections[1].checks[0].evidence=[{artifact_id:original.id,locator:'原文第 1 节'}];
  return {project,root,original,record,template,data};
}

test('captured reports render evidence and mobile without a manual upload form',async({page,request})=>{
  const f=await seed(request),errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{
    const invalid=await request.post(f.root+'/artifacts',{data:{content:JSON.stringify({...f.data,summary:'x'.repeat(401)}),schema_id:f.template.id,record_id:f.record.id}});
    expect(invalid.status()).toBe(422);
    const report=await post(request,f.root+'/artifacts',{content:JSON.stringify(f.data),schema_id:f.template.id,record_id:f.record.id});
    await page.goto(report.view_url);await verifyReading(page,request,f);expect(errors).toEqual([]);
  }finally{await page.close();expect((await request.post(f.root+'/workspace/stop')).ok()).toBeTruthy();expect((await request.delete(f.root)).status()).toBe(204);}
});

async function verifyReading(page,request,f){
  await expect(page.getByRole('heading',{name:f.data.title})).toBeVisible();
  await expect(page.getByRole('region',{name:'六维评价'})).toContainText('已评 0 / 6 维');
  await expect(page.locator('.dimension-item')).toHaveCount(6);
  await expect(page.locator('.document-summary strong')).toHaveText('检查范围：');
  await expect(page.locator('.katex')).toHaveCount(1);
  await page.locator('.document-check summary').click();
  const link=page.getByRole('link',{name:'证据 1 · 原文第 1 节'});
  await expect(link).toBeVisible();
  const evidence=await link.getAttribute('href');
  const exported=await request.get(await page.getByRole('link',{name:'导出 Markdown'}).getAttribute('href'));
  expect(await exported.text()).toContain('未能验证');
  await page.reload();await expect(page.getByRole('heading',{name:f.data.title})).toBeVisible();
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await page.goto(evidence);await expect(page.getByRole('heading',{name:'原始依据'})).toBeVisible();
  await expect(page.locator('.katex')).toHaveCount(1);expect(await page.evaluate(()=>window.reportExecuted)).toBeUndefined();
}

test('reader uses URL project independently of active selection and preserves unavailable target',async({page,request})=>{
  const f=await seed(request);
  try{
    const report=await post(request,f.root+'/artifacts',{content:JSON.stringify(f.data),schema_id:f.template.id,record_id:f.record.id});
    await request.delete(f.root+'/records/'+f.record.id);
    await page.goto(report.view_url);
    await expect(page.getByRole('heading',{name:f.data.title})).toBeVisible();
    await expect(page.locator('.document-context')).toContainText('对象已不可用');
    const unavailable=await request.get(f.root+'/artifacts/artifact:missing/reading');expect(unavailable.status()).toBe(404);
  }finally{await page.close();expect((await request.post(f.root+'/workspace/stop')).ok()).toBeTruthy();expect((await request.delete(f.root)).status()).toBe(204);}
});

for(const width of [1100,390])test(`artifact scroll reaches bottom with wheel and keyboard at ${width}px`,async({page,request})=>{
  const f=await seed(request);
  try{
    await page.setViewportSize({width,height:650});
    f.data.sections[0].markdown='研究范围需要保留限定条件。\n\n'.repeat(35);
    const report=await post(request,f.root+'/artifacts',{content:JSON.stringify(f.data),schema_id:f.template.id,record_id:f.record.id});
    const markdown=await post(request,f.root+'/artifacts',{content:'## 原文\n\n'+('可追溯的研究证据。\n\n'.repeat(80))});
    const schema=`/projects/${encodeURIComponent(f.project.id)}/artifacts/${encodeURIComponent(f.template.id)}`;
    for(const url of [report.view_url,markdown.view_url,schema])await assertReaderScroll(page,url);
    await page.reload();await assertScrollInputs(page);
  }finally{await page.close();expect((await request.post(f.root+'/workspace/stop')).ok()).toBeTruthy();expect((await request.delete(f.root)).status()).toBe(204);}
});

async function assertReaderScroll(page,url){
  await page.goto(url);await page.locator('.document-provenance').waitFor();
  for(const summary of await page.locator('.document-check summary').all())await summary.evaluate(e=>e.click());
  await assertScrollInputs(page);
}

async function assertScrollInputs(page){
  const reader=page.locator('.artifact-page'),end=page.locator('.document-provenance');
  const box=await reader.boundingBox();expect(box.y+box.height).toBeLessThanOrEqual(page.viewportSize().height);
  expect(await reader.evaluate(e=>e.scrollHeight>e.clientHeight)).toBeTruthy();
  await page.mouse.move(page.viewportSize().width/2,400);await page.mouse.wheel(0,100000);
  await expect(end).toBeInViewport({ratio:1});
  await reader.focus();await page.keyboard.press('Control+Home');
  await expect.poll(()=>reader.evaluate(e=>e.scrollTop)).toBe(0);
  await page.keyboard.press('Control+End');await expect(end).toBeInViewport({ratio:1});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
}

test('named Markdown stored as plain text renders tables, math and raw source without altering bytes',async({page,request})=>{
  const f=await seed(request);
  const text='# 文献审查\n\n**局限：**尚未取得全文。\n\n- 核验来源\n- 保留缺口\n\n| 检查 | 结果 |\n| --- | --- |\n| DOI | 待核查 |\n\n\\[\nP=196.29\\,W\n\\]\n\n```python\nprint("**literal**")\n```\n\n<script>window.markdownExecuted=true</script>';
  try{
    const artifact=await post(request,f.root+'/artifacts',{content:text,media_type:'text/plain'});
    await post(request,f.root+'/records',{type:'source',content:{title:'文献',attachments:[{id:artifact.id,name:'review.md'}]},artifact_ids:[artifact.id]});
    await page.goto(artifact.view_url);
    await expect(page.getByRole('heading',{name:'文献审查',exact:true})).toBeVisible();
    await expect(page.locator('.artifact-markdown strong')).toHaveText('局限：');
    await expect(page.locator('.artifact-markdown table')).toHaveCount(1);await expect(page.locator('.katex')).toHaveCount(1);
    await page.getByRole('button',{name:'原文',exact:true}).click();
    await expect(page.locator('.artifact-raw')).toHaveText(text);
    expect(await (await request.get(f.root+'/artifacts/'+artifact.id+'?download=true')).text()).toBe(text);
    await page.getByRole('button',{name:'阅读',exact:true}).click();await page.reload();
    await page.setViewportSize({width:390,height:650});await expect(page.locator('.artifact-markdown table')).toHaveCount(1);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    expect(await page.evaluate(()=>window.markdownExecuted)).toBeUndefined();
  }finally{await page.close();expect((await request.post(f.root+'/workspace/stop')).ok()).toBeTruthy();expect((await request.delete(f.root)).status()).toBe(204);}
});
