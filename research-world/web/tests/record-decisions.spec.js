import {test,expect} from '@playwright/test';

async function post(request,path,data){
  const response=await request.post(path,{data});expect(response.ok(),await response.text()).toBeTruthy();return response.json();
}

test('creation comparison, document and close/reopen preserve the research record',async({page,request})=>{
  const project=await post(request,'/api/v1/projects',{name:`Decisions ${Date.now()}`,question:'核查轨道耗散'}),root=`/api/v1/projects/${project.id}`;
  try{
    const node=await post(request,root+'/records',{type:'direction',content:{title:'比较潮汐耗散时间尺度',text:'固定质量与轨道初值，比较不同潮汐参数下的演化时间。'}});
    await page.goto(`/projects/${encodeURIComponent(project.id)}/records/${encodeURIComponent(node.id)}`);
    await page.getByText('文档属性与 Markdown',{exact:true}).click();await expect(page.locator('.record-document pre')).toContainText('status: open');
    await page.getByRole('button',{name:'提出相关方向',exact:true}).click();await page.getByRole('button',{name:'检查并创建',exact:true}).click();
    await expect(page.getByRole('dialog')).toContainText('发现可能重复的节点');await expect(page.getByRole('dialog')).toContainText('文本相似度 1.000');
    expect((await (await request.get(root+'/records')).json())).toHaveLength(1);await page.getByRole('button',{name:'关闭',exact:true}).click();
    await page.getByRole('button',{name:'关闭节点',exact:true}).click();await page.getByLabel('决定依据').fill('数值复核推翻了原有判断');await page.getByRole('button',{name:'确认关闭',exact:true}).click();
    await expect(page.locator('.record-status')).toContainText('Closed · 不再推进');await expect(page.locator('.research-timeline')).toContainText('数值复核推翻了原有判断');
    await page.getByRole('button',{name:'重新打开',exact:true}).click();await page.getByLabel('决定依据').fill('增加可区分预测，继续检查');await page.getByRole('button',{name:'确认重新打开',exact:true}).click();
    await expect(page.locator('.record-status')).toContainText('Open');await page.reload();await expect(page.locator('.record-status')).toContainText('Open');
    const changes=await (await request.get(root+`/changes?record_id=${encodeURIComponent(node.id)}`)).json();expect(changes.filter(c=>c.kind==='status')).toHaveLength(2);
  }finally{await page.close();await request.post(root+'/workspace/stop');const response=await request.delete(root);expect(response.ok()).toBeTruthy();}
});
