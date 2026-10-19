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
  const record=await post(request,root+'/records',{type:'experiment',content:{title:'历史计算',text:'限定条件下的计算'},artifact_ids:[original.id]});
  const template=(await (await request.get(root+'/artifact-templates')).json())[0];
  const data={...template.example,title:'q049 审计阅读验收',target_artifact_id:original.id,summary:'**检查范围：**本次整理历史证据。\\(P=196.29\\,W\\)'};
  data.sections[1].checks[0].evidence=[{artifact_id:original.id,locator:'原文第 1 节'}];
  return {project,root,original,record,template,data};
}

test('publish from node validates schema and renders immutable report, evidence and mobile',async({page,request})=>{
  const f=await seed(request),errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{
    await page.addInitScript(id=>localStorage.setItem('rw.active_project',id),f.project.id);
    await page.goto(`/map?node=${encodeURIComponent(f.record.id)}`);
    await page.getByRole('button',{name:'发布审计报告'}).click();
    await expect(page.getByRole('button',{name:'下载填写示例'})).toBeEnabled();
    await uploadAndValidate(page,{...f.data,summary:'x'.repeat(401)},false);
    await uploadAndValidate(page,f.data,true);
    await page.getByRole('button',{name:'校验并发布',exact:true}).click();
    const href=await page.getByRole('link',{name:'阅读已发布报告'}).getAttribute('href');
    await page.goto(href);await verifyReading(page,request,f);
    expect(errors).toEqual([]);
  }finally{await page.close();await request.delete(f.root);}
});

async function uploadAndValidate(page,data,valid){
  await page.getByLabel('选择已填写的报告').setInputFiles({name:'audit.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
  await page.getByRole('button',{name:'校验',exact:true}).click();
  if(valid)await expect(page.getByRole('status')).toContainText('校验通过');
  else {await expect(page.getByRole('alert')).toContainText('summary');await expect(page.getByRole('alert')).toContainText('400');}
}

async function verifyReading(page,request,f){
  await expect(page.getByRole('heading',{name:f.data.title})).toBeVisible();
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
  }finally{await page.close();await request.delete(f.root);}
});
