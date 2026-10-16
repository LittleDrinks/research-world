import {test,expect} from '@playwright/test';

const event=(seq,type,data)=>({seq,type,data,turn_id:'turn-one'});
const text=(seq,value)=>event(seq,'delta',{text:value});
const tool=(seq,phase,extra={})=>event(seq,'tool',{id:'call-one',name:'bash',phase,...extra});

async function setup(page,request){
  const project=await (await request.post('/api/v1/projects',{data:{name:'工具时间线验收',question:'验证工作区'}})).json();
  await page.addInitScript(id=>{
    localStorage.setItem('rw.active_project',id);
    window.EventSource=class extends EventTarget{constructor(){super();window.testStream=this;}close(){}};
  },project.id);
  const detail={session:{id:'s-timeline',title:'时间线',messages:[{id:'message',content:'运行脚本'}]},
    run:{turns:[{id:'turn-one',message_id:'message',status:'running',events:[]}]}};
  await page.route('**/sessions/s-timeline',route=>route.fulfill({json:detail}));
  await page.goto('/chat/s-timeline');
  await page.waitForFunction(()=>Boolean(window.testStream));
  return {detail,project};
}

async function emit(page,events){
  await page.evaluate(events=>events.forEach(e=>window.testStream.dispatchEvent(new MessageEvent(e.type,{data:JSON.stringify(e)}))),events);
}

async function order(page){
  return page.locator('.pi-assistant > .pi-text, .pi-assistant > .pi-tool').evaluateAll(nodes=>nodes.map(n=>n.className));
}

test('tool starts inline, updates live, and survives replay without duplicate answers',async({page,request})=>{
  const {detail,project}=await setup(page,request);
  try{
    const first=[text(1,'先运行脚本。'),tool(2,'started',{arguments:{command:'python hello.py'}})];
    await emit(page,first);
    await expect(page.locator('.pi-tool summary')).toContainText('进行中');
    expect(await order(page)).toEqual(['pi-text','pi-tool']);
    const update=tool(3,'updated',{partial_result:{content:[{type:'text',text:'hello-world'}]}});
    await emit(page,[update]);
    await expect(page.locator('.pi-tool pre').last()).toHaveText('hello-world');
    const last=[tool(4,'completed',{result:{content:[{type:'text',text:'hello-world'}]},is_error:false}),text(5,'执行成功。')];
    detail.run.turns[0].events=[...first,update,...last];
    await emit(page,[...first,...last]);
    await expect(page.locator('.pi-tool')).toHaveCount(1);
    await expect(page.locator('.pi-text')).toHaveText(['先运行脚本。','执行成功。']);
    expect(await order(page)).toEqual(['pi-text','pi-tool','pi-text']);
    detail.run.turns[0].status='completed';detail.session.messages[0].assistant_response='执行成功。';
    await page.reload();
    await expect(page.locator('.pi-text')).toHaveText(['先运行脚本。','执行成功。']);
    expect(await order(page)).toEqual(['pi-text','pi-tool','pi-text']);
  }finally{await request.delete(`/api/v1/projects/${project.id}`);}
});
