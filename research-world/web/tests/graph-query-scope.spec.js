import {randomUUID} from 'node:crypto';
import {test,expect} from '@playwright/test';

async function post(request,path,data){
  const response=await request.post(path,{data});expect(response.ok(),await response.text()).toBeTruthy();return response.json();
}

test('map includes records beyond fifty and clearing an empty search restores them',async({page,request})=>{
  const project=await post(request,'/api/v1/projects',{name:`Query scope ${randomUUID()}`,question:'Compare orbital mechanisms'});
  const root=`/api/v1/projects/${project.id}`;
  try{
    for(let i=0;i<51;i++)await post(request,root+'/records',{type:'question',content:{title:randomUUID()}});
    const last=await post(request,root+'/records',{type:'experiment',content:{title:'Late-time orbital precession'}});
    await page.goto(`/projects/${encodeURIComponent(project.id)}/map?node=${encodeURIComponent(last.id)}&view=focus`);
    await expect(page.locator('.map-toolbar')).toContainText('52 个记录');
    await expect(page.locator(`.react-flow__node[data-id="${last.id}"]`)).toHaveCount(1);
    const search=page.getByRole('searchbox',{name:'检索局部地图'});
    await search.fill('当前研究项目所有对象与关系');await page.getByRole('button',{name:'检索',exact:true}).click();
    await expect(page.locator('.map-toolbar')).toContainText('匹配 0 / 项目 52');
    await search.fill('');await page.getByRole('button',{name:'检索',exact:true}).click();
    await expect(page.locator('.map-toolbar')).toContainText('52 个记录');
    await expect(page.locator('.map-toolbar')).not.toContainText('匹配 0');
  }finally{
    await page.close();await request.post(root+'/workspace/stop');
    expect((await request.delete(root)).ok()).toBeTruthy();
  }
});
