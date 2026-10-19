import {test,expect} from '@playwright/test';

test('delete a saved Agent with confirmation and refresh both selectors',async({page,request})=>{
  const project=await (await request.post('/api/v1/projects',{data:{name:`Agent deletion ${Date.now()}`,question:'Configuration only'}})).json();
  const profiles=await (await request.get('/api/v1/agents')).json(),base=profiles.find(p=>p.id==='research-assistant');
  const agent={...base,id:`delete-test-${Date.now()}`,name:`可删除配置 ${Date.now()}`};
  expect((await request.put(`/api/v1/agents/${agent.id}`,{data:agent})).ok()).toBeTruthy();
  try{
    await page.addInitScript(id=>localStorage.setItem('rw.active_project',id),project.id);await page.goto('/agents/'+agent.id);
    const button=page.getByRole('button',{name:'删除配置',exact:true});await expect(button).toBeEnabled({timeout:90000});
    await button.click();await expect(page.getByRole('dialog')).toContainText(agent.name);await page.getByRole('button',{name:'取消',exact:true}).click();
    await expect(page.getByLabel('选择 Agent')).toHaveValue(agent.id);
    await failedDelete(page,agent.id);await page.getByRole('button',{name:'确认删除配置',exact:true}).click();
    await expect(page).toHaveURL(/\/agents\/research-assistant$/);await expect(page.getByRole('option',{name:agent.name,exact:true})).toHaveCount(0);
    await expect(page.locator('.record-items')).not.toContainText(agent.name);await page.reload();await expect(button).toBeDisabled();
    expect((await (await request.get('/api/v1/agents')).json()).some(a=>a.id===agent.id)).toBeFalsy();
    await page.getByRole('button',{name:'复制为新 Agent'}).click();await expect(button).toBeDisabled();
  }finally{await page.close();await request.delete(`/api/v1/agents/${agent.id}`);await request.post(`/api/v1/projects/${project.id}/workspace/stop`);await request.delete(`/api/v1/projects/${project.id}`);}
});

async function failedDelete(page,id){
  await page.getByRole('button',{name:'删除配置',exact:true}).click();
  await page.route(`**/api/v1/agents/${id}`,route=>route.fulfill({status:503,json:{detail:'暂时无法删除'}}),{times:1});
  await page.getByRole('button',{name:'确认删除配置',exact:true}).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toHaveText('暂时无法删除');
  await expect(page.getByLabel('选择 Agent')).toHaveValue(id);
}
