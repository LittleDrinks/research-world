import {test,expect} from '@playwright/test';

const event=(seq,type,data)=>({seq,type,turn_id:'t',data});
async function fixture(page,events,answer='') {
  await page.addInitScript(()=>{localStorage.setItem('rw.active_project','presentation');window.EventSource=class extends EventTarget{constructor(){super();window.testStream=this;}close(){}};});
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:'presentation',projects:[{id:'presentation',name:'排版'}],sessions:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  await page.route('**/api/v1/projects/*/workspace',r=>r.fulfill({json:{status:'ready',url:'/lab'}}));
  const detail={session:{project_id:'presentation',id:'s-presentation',title:'排版',messages:[{id:'m',content:'<thinking>用户示例</thinking>',assistant_response:answer}]},run:{turns:[{id:'t',message_id:'m',status:'running',events}]}};
  await page.route('**/sessions/s-presentation',r=>r.fulfill({json:detail}));
  await page.goto('/chat/s-presentation');
  return detail;
}
async function emit(page,value) {
  await page.evaluate(e=>window.testStream.dispatchEvent(new MessageEvent(e.type,{data:JSON.stringify(e)})),value);
}

test('message column remains centered with composer on wide and narrow screens',async({page})=>{
  await page.setViewportSize({width:1920,height:1080});await fixture(page,[], '正式回复。');
  await expect(page.locator('.pi-assistant')).toBeVisible();
  const box=await page.locator('.pi-transcript').boundingBox(),input=await page.locator('.pi-composer').boundingBox();
  expect(box.width).toBeLessThanOrEqual(900);
  expect(Math.abs(box.x+box.width/2-input.x-input.width/2)).toBeLessThan(12);
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});

test('tagged thinking stays collapsed across deltas, tools and replay',async({page})=>{
  const start=event(1,'delta',{text:'开始。<think'}),detail=await fixture(page,[start]);
  await page.waitForFunction(()=>Boolean(window.testStream));
  const thought=event(2,'delta',{text:'ing>内部检查'});await emit(page,thought);
  await expect(page.locator('.thinking-body')).toBeHidden();
  const tool=event(3,'tool',{id:'tool',name:'graph',phase:'completed',arguments:{},result:{}});await emit(page,tool);
  const end=event(4,'delta',{text:'继续检查</thinking>正式结论。'});await emit(page,end);
  await expect(page.locator('.pi-assistant')).toContainText('正式结论。');
  await expect(page.locator('.pi-assistant')).not.toContainText('<thinking>');
  expect((await page.locator('.pi-assistant .pi-text').allTextContents()).join('')).not.toContain('继续检查');
  await page.locator('.pi-thinking summary').first().click();await expect(page.getByText('内部检查',{exact:true})).toBeVisible();
  detail.run.turns[0].events.push(thought,tool,end);detail.run.turns[0].status='completed';await page.reload();
  await expect(page.locator('.thinking-body').first()).toBeHidden();
  await expect(page.locator('.pi-tool')).toHaveCount(1);
  await expect(page.locator('.pi-user')).toContainText('<thinking>用户示例</thinking>');
});

test('saved replies preserve literal tags in code, escaping and math',async({page})=>{
  const literal='`<thinking>inline</thinking>`\n\n```text\n<thinking>fenced</thinking>\n```\n\n'+String.raw`\<thinking>escaped\</thinking>`;
  await fixture(page,[], '<thinking>隐藏的内容</thinking>正文。\n\n'+literal+'\n\n'+String.raw`\(\text{<thinking>}\)`);
  await expect(page.locator('.pi-thinking')).toHaveCount(1);await expect(page.locator('.thinking-body')).toBeHidden();
  await expect(page.locator('.pi-assistant code')).toHaveText(['<thinking>inline</thinking>','<thinking>fenced</thinking>\n']);
  await expect(page.locator('.pi-assistant')).toContainText('<thinking>escaped</thinking>');
  await expect(page.locator('.pi-assistant .katex')).toHaveCount(1);
});

test('thinking-only events do not duplicate saved output and nested code remains literal',async({page})=>{
  const source='<thinking>内部检查\n```text\n</thinking>\n```\n继续检查</thinking>';
  await fixture(page,[event(1,'delta',{text:source})],source);
  await expect(page.locator('.pi-thinking')).toHaveCount(1);
  await expect(page.locator('.thinking-body')).toBeHidden();
  await page.locator('.pi-thinking summary').click();
  await expect(page.locator('.thinking-body code')).toHaveText('</thinking>\n');
  await expect(page.locator('.thinking-body')).toContainText('继续检查');
});

test('child results fold their own tagged thinking without affecting the parent answer',async({page})=>{
  await fixture(page,[event(1,'child_result',{status:'completed',result_text:'<think>子任务检查</think>子任务结论。'}),event(2,'delta',{text:'主结论。'})]);
  await expect(page.locator('.pi-child .pi-thinking')).toHaveCount(1);
  await expect(page.locator('.pi-child .thinking-body')).toBeHidden();
  await expect(page.locator('.child-result-body')).toContainText('子任务结论。');
  await expect(page.locator('.pi-assistant > .pi-text')).toHaveText('主结论。');
});

test('a thinking marker split around a tool cannot expose its body',async({page})=>{
  const tool=event(2,'tool',{id:'tool',name:'graph',phase:'completed',arguments:{},result:{}});
  await fixture(page,[event(1,'delta',{text:'<think'}),tool,event(3,'delta',{text:'ing>内部检查</thinking>正式结论。'})]);
  await expect(page.locator('.pi-thinking')).toHaveCount(1);
  await expect(page.locator('.thinking-body')).toBeHidden();
  expect((await page.locator('.pi-assistant').innerText())).not.toContain('内部检查');
  await expect(page.locator('.pi-assistant > .pi-text')).toHaveText('正式结论。');
  await expect(page.locator('.pi-tool')).toHaveCount(1);
});

test('code-fence context survives a tool inside a thinking section',async({page})=>{
  const first=event(1,'delta',{text:'<thinking>检查\n```text\n'});
  const tool=event(2,'tool',{id:'tool',name:'graph',phase:'completed',arguments:{},result:{}});
  const last=event(3,'delta',{text:'</thinking>\n```\n仍在思考</thinking>正式结论。'});
  const detail=await fixture(page,[first,tool,last]);
  await expect(page.locator('.pi-thinking')).toHaveCount(2);
  expect(await page.locator('.pi-assistant').innerText()).not.toContain('仍在思考');
  await expect(page.locator('.pi-assistant > .pi-text')).toHaveText('正式结论。');
  detail.run.turns[0].status='completed';await page.reload();
  expect(await page.locator('.pi-assistant').innerText()).not.toContain('仍在思考');
  await expect(page.locator('.pi-assistant > .pi-text')).toHaveText('正式结论。');
});
