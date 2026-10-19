import {test,expect} from '@playwright/test';

const project='markdown-preview';
const answer='- **计算可复现：**在孤立近似下，功率约 **196.29 W**。\n- **论证需限定：**不能外推。\n\n**下一步：**核对原文。\n\n中文**“引用”**接正文，**（范围）**也加粗。\n\n`**计算可复现：**代码`\n\n```text\n**下一步：**代码块\n```\n\n\\*\\*字面星号：\\*\\*正文\n\n[脚本](/workspace/check.py) [报告](/api/v1/projects/markdown-preview/artifacts/example)\n\n<script>window.markdownExecuted=true</script>';

async function fixture(page,events=[]) {
  await page.addInitScript(()=>{localStorage.setItem('rw.active_project','markdown-preview');window.EventSource=class extends EventTarget{constructor(){super();window.testStream=this;}close(){}};});
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:project,projects:[{id:project,name:'中文排版'}],sessions:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  await page.route('**/api/v1/projects/*/workspace',r=>r.fulfill({json:{status:'ready',url:'/lab'}}));
  const detail={session:{project_id:project,id:'s-markdown',title:'审计结果',messages:[{id:'m',content:'审计结果',assistant_response:events.length?'':answer}]},
    run:{turns:[{id:'t',message_id:'m',status:events.length?'running':'completed',events}]}};
  await page.route('**/sessions/s-markdown',r=>r.fulfill({json:detail}));
  await page.goto('/chat/s-markdown');
  return detail;
}

async function assertAnswer(page) {
  const rendered=page.locator('.pi-assistant');
  for(const text of ['计算可复现：','论证需限定：','下一步：','“引用”','（范围）','196.29 W']) await expect(rendered.locator('strong').filter({hasText:text})).toHaveCount(1);
  await expect(rendered.locator('code')).toHaveText(['**计算可复现：**代码','**下一步：**代码块\n']);
  await expect(rendered).toContainText('**字面星号：**正文');
  await expect(rendered.getByRole('link',{name:'脚本'})).toHaveAttribute('href','/workspace/check.py?project=markdown-preview');
  await expect(rendered.getByRole('link',{name:'报告'})).toHaveAttribute('href','/api/v1/projects/markdown-preview/artifacts/example');
  expect(await page.evaluate(()=>window.markdownExecuted)).toBeUndefined();
}

test('CJK emphasis renders with adjacent punctuation while code and links remain literal',async({page})=>{
  await fixture(page);
  await assertAnswer(page);
  await page.reload();
  await assertAnswer(page);
});

test('streamed CJK emphasis and child results use the same parser after replay',async({page})=>{
  const events=[{seq:1,type:'delta',turn_id:'t',data:{text:'**计算可复现：'}}];
  const detail=await fixture(page,events);
  await page.waitForFunction(()=>Boolean(window.testStream));
  await expect(page.locator('.pi-text')).toContainText('计算可复现：');
  const last={seq:2,type:'delta',turn_id:'t',data:{text:'**在圆轨道近似下成立。'}};
  await page.evaluate(event=>window.testStream.dispatchEvent(new MessageEvent(event.type,{data:JSON.stringify(event)})),last);
  await expect(page.locator('.pi-text strong')).toHaveText('计算可复现：');
  const child={seq:3,type:'child_result',turn_id:'t',data:{result_text:'**子审计：**仅适用于圆轨道。'}};
  await page.evaluate(event=>window.testStream.dispatchEvent(new MessageEvent(event.type,{data:JSON.stringify(event)})),child);
  await expect(page.locator('.pi-child strong')).toHaveText('子审计：');
  detail.run.turns[0].events.push(last,child);detail.run.turns[0].status='completed';
  await page.reload();
  await expect(page.locator('.pi-text strong')).toHaveText('计算可复现：');
  await expect(page.locator('.pi-child strong')).toHaveText('子审计：');
});
