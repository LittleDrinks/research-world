import {test,expect} from '@playwright/test';

async function post(request,path,data){
  const r=await request.post(path,{data});expect(r.ok(),await r.text()).toBeTruthy();return r.json();
}

async function fixture(request){
  const p=await post(request,'/api/v1/projects',{name:`Coverage ${Date.now()}`,question:'Compare methods'}),root='/api/v1/projects/'+p.id;
  const artifact=await post(request,root+'/artifacts',{content:'## 已完成的检查\n输入和结果可回查。'});
  const records=[];for(const title of ['solar orbit dynamics','solar orbit integrator','tidal energy','stellar evolution'])records.push(await post(request,root+'/records',{type:'source',content:{title,text:'来源',canonical_url:'https://example.org/'+encodeURIComponent(title)},artifact_ids:[]}));
  const target=await post(request,root+'/records',{type:'direction',content:{title:'方法比较',text:'比较范围与结果',attachments:[{id:artifact.id,name:'核查结果.md'}]},artifact_ids:[artifact.id]});
  const conditions=[];for(const rule of ['AND','OR','k-of-N'])conditions.push(await post(request,root+'/joint-conditions',{title:rule+' 条件',rule,k:rule==='k-of-N'?2:null,target_id:target.id,members:records.slice(0,3).map(r=>({record_id:r.id,role:r.content.title})),statement:'比较条件',rationale:'共同约束目标',evidence:[{artifact_id:artifact.id,locator:'检查结果'}]}));
  return {project:p.id,root,records,target,conditions};
}

test('semantic components have selectable conditions, source selection and result previews',async({page,request})=>{
  const f=await fixture(request);
  try{
    await page.goto(`/projects/${encodeURIComponent(f.project)}/map?node=${encodeURIComponent(f.target.id)}`);
    await expect(page.locator('.joint-node')).toHaveCount(3,{timeout:60000});await expect(page.locator('.research-node')).toHaveCount(4);
    await page.getByRole('button',{name:'聚焦选中关系'}).click();await expect(page.getByRole('button',{name:'显示研究主线'})).toBeVisible();
    await page.getByRole('button',{name:'条件列表 · 3',exact:true}).click();
    for(const condition of f.conditions){await page.locator('.joint-list .joint-list-item').filter({hasText:condition.title}).click();await expect(page.locator('.joint-inspector h1')).toHaveText(condition.title);}
    await page.getByRole('button',{name:'文献 · 4',exact:true}).click();await page.getByRole('button',{name:'MMR 选择阅读候选'}).click();
    await page.getByLabel('选择数量',{exact:true}).fill('2');await page.getByRole('button',{name:'运行选择',exact:true}).click();await expect(page.getByRole('dialog').locator('tbody tr')).toHaveCount(2);
    await page.getByRole('button',{name:'关闭',exact:true}).click();await page.goto('/settings');await page.getByRole('button',{name:'研究成果',exact:true}).click();await expect(page.getByRole('dialog')).toContainText('核查结果.md');
    await page.goto(`/projects/${encodeURIComponent(f.project)}/records/${encodeURIComponent(f.target.id)}`);
    await page.locator('.record-assets').getByRole('button',{name:'预览',exact:true}).click();await expect(page.locator('.asset-preview')).toContainText('已完成的检查');
    await page.setViewportSize({width:390,height:844});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  }finally{await page.close();await request.post(f.root+'/workspace/stop');await request.delete(f.root);}
});

test('record results preview executable code, quoted CSV and an image',async({page,request})=>{
  const f=await fixture(request);
  try{
    const inputs=[['text/x-python','print(42)'],['text/csv','method,error\n"Leapfrog, 200",0.0001\n']];
    for(const [media_type,content] of inputs)await post(request,f.root+'/artifacts',{media_type,content,record_id:f.target.id});
    await post(request,f.root+'/artifacts',{media_type:'image/png',record_id:f.target.id,content_base64:'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='});
    await page.goto(`/projects/${encodeURIComponent(f.project)}/records/${encodeURIComponent(f.target.id)}`);
    const rows=page.locator('.record-asset');await expect(rows).toHaveCount(4);
    await rows.nth(1).getByRole('button',{name:'预览',exact:true}).click();await expect(rows.nth(1).locator('pre')).toHaveText('print(42)');
    await rows.nth(2).getByRole('button',{name:'预览',exact:true}).click();await expect(rows.nth(2).locator('tbody tr')).toContainText('Leapfrog, 200');
    await rows.nth(3).getByRole('button',{name:'预览',exact:true}).click();await expect.poll(()=>rows.nth(3).locator('img').evaluate(n=>n.complete&&n.naturalWidth>0)).toBeTruthy();
  }finally{await page.close();await request.post(f.root+'/workspace/stop');await request.delete(f.root);}
});
