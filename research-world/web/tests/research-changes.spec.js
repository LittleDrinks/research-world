import {test,expect} from '@playwright/test';

async function post(request,path,data){
  const response=await request.post(path,{data});expect(response.ok(),await response.text()).toBeTruthy();return response.json();
}

async function seed(request){
  const p=await post(request,'/api/v1/projects',{name:`Changes ${Date.now()}-${Math.random()}`,question:'Related questions'});
  const root=`/api/v1/projects/${p.id}`;
  const artifact=await post(request,root+'/artifacts',{content:'# 原文证据'});
  const record=await post(request,root+'/records',{type:'direction',content:{title:'待核查的解释',text:'**初稿：**模型前提尚未对齐。'},artifact_ids:[artifact.id]});
  return {project:p.id,root,record};
}

test('manage labels and versioned research changes inside existing map',async({page,request})=>{
  const f=await seed(request),errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{
    await page.addInitScript(id=>localStorage.setItem('rw.active_project',id),f.project);
    await page.goto('/map?node='+encodeURIComponent(f.record.id));
    await manageAndAssign(page);await reviseAndDiscuss(page);await renameAndDelete(page);
    await page.locator('.map-toolbar-actions').getByRole('button',{name:'Changes',exact:true}).click();
    await expect(page.getByRole('dialog',{name:'项目 Changes'})).toContainText('删除项目标签并移除关联');
    await page.getByRole('button',{name:'关闭',exact:true}).click();
    await page.setViewportSize({width:390,height:844});
    await page.locator('.inspector').scrollIntoViewIfNeeded();
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    await page.reload();await expect(page.locator('.inspector-header')).toContainText('限定后的解释');expect(errors).toEqual([]);
  }finally{await page.close();await request.post(f.root+'/workspace/stop');await request.delete(f.root);}
});

async function manageAndAssign(page){
  await page.getByRole('button',{name:'管理标签',exact:true}).click();
  for(const name of ['warning','need-grill']){
    await page.getByLabel('标签名称',{exact:true}).fill(name);await page.getByLabel('标签说明',{exact:true}).fill('用户定义的关注点');
    await page.getByRole('button',{name:'创建标签',exact:true}).click();await expect(page.locator('.label-manager-list')).toContainText(name);
  }
  await page.getByRole('button',{name:'关闭',exact:true}).click();await page.getByRole('button',{name:'设置标签',exact:true}).click();
  await page.getByRole('dialog').getByLabel(/warning/).check();await page.getByRole('dialog').getByLabel(/need-grill/).check();
  await page.getByLabel('变更原因',{exact:true}).fill('需要质疑当前模型前提');await page.getByRole('button',{name:'保存标签关联'}).click();
  await expect(page.locator('.record-label-badges .research-label')).toHaveCount(2);
}

async function reviseAndDiscuss(page){
  await page.getByRole('button',{name:'编辑正文',exact:true}).click();
  await page.getByLabel('标题',{exact:true}).fill('限定后的解释');await page.getByLabel('正文（Markdown）',{exact:true}).fill('**范围：**只讨论已明确条件的模型。');
  await page.getByLabel('修订原因',{exact:true}).fill('明确适用条件');await page.getByRole('button',{name:'保存修订'}).click();
  await expect(page.locator('.inspector-header')).toContainText('限定后的解释');
  await page.getByRole('button',{name:'初始版本',exact:true}).click();await expect(page.locator('.node-body')).toContainText('初稿');
  await page.locator('.record-workspace-tabs').getByRole('button',{name:'讨论',exact:true}).click();
  await page.getByLabel('评论 · 引用 r1',{exact:true}).fill('这条评论固定针对初稿，尚需补信息。');await page.getByRole('button',{name:'发表评论'}).click();
  await expect(page.locator('.record-discussion article')).toContainText('引用 r1');
  await page.getByRole('button',{name:'返回当前',exact:true}).click();
  await page.locator('.record-workspace-tabs').getByRole('button',{name:'Changes',exact:true}).click();
  await expect(page.locator('.record-changes')).toContainText('明确适用条件');
}

async function renameAndDelete(page){
  await page.getByRole('button',{name:'管理标签',exact:true}).click();
  const row=page.locator('.label-manager-list li').filter({hasText:'warning'});
  await row.getByRole('button',{name:'编辑',exact:true}).click();await page.getByLabel('标签名称',{exact:true}).fill('需核查');
  await page.getByRole('button',{name:'保存标签',exact:true}).click();
  await page.locator('.label-manager-list li').filter({hasText:'需核查'}).getByRole('button',{name:'删除',exact:true}).click();
  await page.getByRole('button',{name:'确认删除标签'}).click();await expect(page.locator('.label-manager-list')).not.toContainText('需核查');
  await page.getByRole('button',{name:'关闭',exact:true}).click();await expect(page.locator('.record-label-badges .research-label')).toHaveCount(1);
  await page.getByRole('button',{name:'r2',exact:true}).click();await expect(page.locator('.fixed-record')).toContainText('warning');
}

test('concurrent edit reports conflict and retains the local draft',async({page,request})=>{
  const f=await seed(request);
  try{
    await page.addInitScript(id=>localStorage.setItem('rw.active_project',id),f.project);
    await page.goto('/map?node='+encodeURIComponent(f.record.id));await page.getByRole('button',{name:'编辑正文',exact:true}).click();
    await page.getByLabel('正文（Markdown）',{exact:true}).fill('不能被覆盖的本地草稿');await page.getByLabel('修订原因',{exact:true}).fill('本地修改');
    await post(request,f.root+`/records/${f.record.id}/changes`,{kind:'revise',base_revision:1,reason:'另一处修改',title:'服务端新版本',text:'服务端内容'});
    await page.getByRole('button',{name:'保存修订'}).click();await expect(page.getByRole('dialog').getByRole('alert')).toContainText('记录已更新');
    await expect(page.getByLabel('正文（Markdown）',{exact:true})).toHaveValue('不能被覆盖的本地草稿');
  }finally{await page.close();await request.post(f.root+'/workspace/stop');await request.delete(f.root);}
});
