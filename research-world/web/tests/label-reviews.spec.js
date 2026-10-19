import {test,expect} from '@playwright/test';

async function json(response){expect(response.ok(),await response.text()).toBeTruthy();return response.json();}
async function seed(request){
  const project=await json(await request.post('/api/v1/projects',{data:{name:`Review UI ${Date.now()}`,question:'How to check energy drift?'}}));
  const root=`/api/v1/projects/${project.id}`;
  const label=await json(await request.post(root+'/labels',{data:{name:'need-review',color:'#8050c0',description:'请求独立复核当前版本'}}));
  const record=await json(await request.post(root+'/records',{data:{type:'experiment',content:{title:'积分误差检查',text:'核查长期积分的能量误差。'}}}));
  return {project:project.id,root,label,record};
}
async function cleanup(request,f){
  const rules=await json(await request.get(f.root+'/review-rules'));
  for(const rule of rules)await request.put(f.root+'/review-rules/'+rule.label_id,{data:{enabled:false,agent_id:rule.config.agent.id,schema_id:rule.config.schema_id}});
  await request.post(f.root+'/workspace/stop');await request.delete(f.root);
}

// Binding and label interactions use the real control API. No model is started.
test('bind a label, preview model invocation, rename it and disable automation',async({page,request})=>{
  const f=await seed(request);
  try{
    await page.addInitScript(id=>localStorage.setItem('rw.active_project',id),f.project);
    await page.goto('/settings');await page.getByRole('button',{name:'管理标签',exact:true}).click();
    await page.locator('.label-manager-list li').filter({hasText:'need-review'}).getByRole('button',{name:'自动复核'}).click();
    await expect(page.getByLabel('复核 Agent')).toBeVisible();
    await page.getByLabel('启用：新增标签后自动调用模型').check();
    await page.getByRole('button',{name:'保存复核绑定'}).click();await expect(page.getByRole('status')).toContainText('绑定已保存');
    const rules=await json(await request.get(f.root+'/review-rules'));expect(rules[0].enabled).toBe(true);
    await request.put(f.root+'/labels/'+f.label.id,{data:{name:'请复核',color:'#8050c0',description:'复核当前版本'}});
    await page.goto(`/projects/${encodeURIComponent(f.project)}/records/${encodeURIComponent(f.record.id)}`);
    await page.getByRole('button',{name:'设置标签',exact:true}).click();await page.getByRole('dialog').getByLabel(/请复核/).check();
    await expect(page.getByRole('note')).toContainText('保存后将启动独立复核');
    await expect(page.getByRole('note')).toContainText(rules[0].config.agent.model);
    await page.getByRole('button',{name:'关闭',exact:true}).click();
    expect(await json(await request.get(f.root+`/records/${f.record.id}/reviews`))).toEqual([]);
    await page.goto('/settings');await page.getByRole('button',{name:'管理标签',exact:true}).click();
    await page.getByRole('button',{name:'自动复核'}).click();await page.getByLabel('启用：新增标签后自动调用模型').uncheck();
    await page.getByRole('button',{name:'保存复核绑定'}).click();await expect(page.getByRole('status')).toContainText('绑定已保存');
    await page.setViewportSize({width:390,height:844});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    await page.screenshot({path:'test-results/review-binding-mobile.png'});
    await page.goto(`/projects/${encodeURIComponent(f.project)}/records/${encodeURIComponent(f.record.id)}`);
    await page.getByRole('button',{name:'设置标签',exact:true}).click();await page.getByRole('dialog').getByLabel(/请复核/).check();
    await expect(page.getByRole('note')).toHaveCount(0);await page.getByLabel('变更原因',{exact:true}).fill('人工复核请求');
    await page.getByRole('button',{name:'保存标签关联'}).click();await expect(page.locator('.record-label-badges')).toContainText('请复核');
    expect(await json(await request.get(f.root+`/records/${f.record.id}/reviews`))).toEqual([]);
  }finally{await page.close();await cleanup(request,f);}
});

// Runtime outcomes are controlled here; backend tests exercise dispatch and report writeback.
test('review task states expose scope, execution and a readable report',async({page,request})=>{
  const f=await seed(request);
  try{
    const target=await json(await request.post(f.root+'/artifacts',{data:{record_id:f.record.id,content:'# 积分结果\n需要检查误差来源。'}}));
    const templates=await json(await request.get(f.root+'/artifact-templates'));
    const data={...templates[0].example,title:'积分误差复核',summary:'尚缺积分误差序列，当前无法判定。',target_artifact_id:target.id};
    const report=await json(await request.post(f.root+'/artifacts',{data:{record_id:f.record.id,schema_id:templates[0].id,content:JSON.stringify(data)}}));
    let state='running';
    await page.route('**/records/*/reviews',route=>route.fulfill({json:[{id:'review-ui',revision:1,status:state,agent_name:'复核助手',model:'test/model',run_id:'run-ui',session_id:'s-ui',target_id:target.id,report_id:state==='completed'?report.id:null,input_changed:state==='completed',error:state==='failed'?'运行中断；请求标签保留':''}]}));
    await page.goto(`/projects/${encodeURIComponent(f.project)}/records/${encodeURIComponent(f.record.id)}`);
    const task=page.locator('.review-task');await expect(task).toContainText('复核中');await expect(task.getByRole('link',{name:'执行过程'})).toBeVisible();
    state='failed';await expect(task).toContainText('复核中断');await expect(task.getByRole('button',{name:'重试复核'})).toBeVisible();
    state='completed';await expect(task).toContainText('复核完成');await expect(task).toContainText('尚未覆盖当前修改');
    await expect(task.getByRole('button',{name:'取消任务'})).toHaveCount(0);
    await page.setViewportSize({width:390,height:844});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    await task.screenshot({path:'test-results/review-result-mobile.png'});
    await page.goto(report.view_url);await expect(page.getByRole('heading',{name:'积分误差复核',exact:true})).toBeVisible();
    await expect(page.locator('body')).toContainText('尚缺积分误差序列');
  }finally{await page.close();await cleanup(request,f);}
});
