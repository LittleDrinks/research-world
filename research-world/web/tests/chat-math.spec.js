import {test,expect} from '@playwright/test';

const math=String.raw`## 结论

**\(3.374\times10^{30}\) s**，以及 $P=196.291$。

\[
P_{\rm GW}=\frac{32}{5}\frac{G^4}{c^5}\frac{m_1^2m_2^2(m_1+m_2)}{a^5}
\]

$$
t=\frac{5}{256}\frac{c^5a^4}{G^3m_1m_2(m_1+m_2)}
$$

- 能量：
  \[
  E=\frac{GMm}{2a}
  \]

\[x=\underbrace{a+a+a+a+a+a+a+a+a+a+a+a+a+a+a+a+a+a+a+a+a+a}_{long}\]

代码：CODE_SAMPLE

**限制：**圆轨道。`.replace('CODE_SAMPLE','`'+String.raw`\(literal\)`+'`');

async function fixture(page,events) {
  await page.addInitScript(()=>{localStorage.setItem('rw.active_project','math');window.EventSource=class extends EventTarget{constructor(){super();window.testStream=this;}close(){}};});
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:'math',projects:[{id:'math',name:'公式'}],sessions:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  await page.route('**/api/v1/projects/*/workspace',r=>r.fulfill({json:{status:'ready',url:'/lab'}}));
  const detail={session:{project_id:'math',id:'s-math',title:'公式',messages:[{id:'m',content:'复算',assistant_response:''}]},
    run:{turns:[{id:'t',message_id:'m',status:'running',events}]}};
  await page.route('**/sessions/s-math',r=>r.fulfill({json:detail}));
  await page.goto('/chat/s-math');
  return detail;
}
const child=(seq,status,result_text)=>({seq,type:'child_result',turn_id:'t',data:{child_run_id:`r-${seq}`,status,result_text}});

test('child report cards render all math delimiters and keep long formulas local',async({page})=>{
  await fixture(page,[child(1,'completed',math),child(2,'error','无法完成独立核验')]);
  await expect(page.locator('.pi-child .katex')).toHaveCount(6);
  await expect(page.locator('.pi-child .katex-display')).toHaveCount(4);
  await expect(page.locator('.pi-child strong .katex')).toHaveCount(1);
  await expect(page.locator('.pi-child code')).toHaveText(String.raw`\(literal\)`);
  const completed=page.locator('details.pi-child').first();
  await expect(completed.locator('summary')).toContainText('完成');
  await expect(page.locator('details.pi-child').last().locator('summary')).toContainText('失败');
  await completed.locator('summary').click();await expect(completed.locator('.child-result-body')).toBeHidden();
  await completed.locator('summary').click();await expect(completed.locator('.child-result-body')).toBeVisible();
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await expect(page.locator('.pi-child h2').first()).toHaveText('结论');
});

test('unfinished streamed formula completes and survives replay',async({page})=>{
  const first={seq:1,type:'delta',turn_id:'t',data:{text:String.raw`结果 \(\frac{1}{`}};
  const detail=await fixture(page,[first]);await page.waitForFunction(()=>Boolean(window.testStream));
  const last={seq:2,type:'delta',turn_id:'t',data:{text:String.raw`2}\) 成立。`}};
  await page.evaluate(e=>window.testStream.dispatchEvent(new MessageEvent(e.type,{data:JSON.stringify(e)})),last);
  await expect(page.locator('.pi-text .katex')).toHaveCount(1);
  detail.run.turns[0].events.push(last);detail.run.turns[0].status='completed';
  await page.reload();await expect(page.locator('.pi-text .katex')).toHaveCount(1);
});

test('invalid TeX stays local, fenced math stays literal and unsafe math links remain inert',async({page})=>{
  const source=String.raw`\[\frac{1}{\]`+'\n\n正文继续。\n\n```text\n'+String.raw`\[literal\]`+'\n```\n\n'+String.raw`\(\href{javascript:alert(1)}{unsafe}\)`;
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await fixture(page,[child(1,'completed',source)]);
  await expect(page.locator('.katex-error')).toHaveCount(1);
  await expect(page.locator('.child-result-body')).toContainText('正文继续。');
  await expect(page.locator('.child-result-body pre code')).toHaveText(String.raw`\[literal\]`+'\n');
  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('execution-limit child status and math-tagged code fences remain explicit',async({page})=>{
  const source='```math\nx^2 + y^2\n```\n\n'+String.raw`\(z^2\)`;
  await fixture(page,[child(1,'limit',source)]);
  await expect(page.locator('.pi-child summary')).toContainText('达到执行上限');
  await expect(page.locator('.pi-child pre code')).toHaveText('x^2 + y^2\n');
  await expect(page.locator('.pi-child .katex')).toHaveCount(1);
});
