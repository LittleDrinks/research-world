import {test,expect} from '@playwright/test';

const records=['A','B','target'].map((id,index)=>({id,type:index<2?'source':'direction',content:{title:id,text:'动画验收'},artifact_ids:[]}));
const relations=['supports','refutes','depends_on'].map(type=>({id:type,source_id:'A',target_id:'target',type}));
const joint_conditions=['AND','OR','k-of-N'].map(rule=>({id:`joint:${rule}`,title:rule,rule,k:rule==='k-of-N'?1:null,
  members:[{record_id:'A',role:'条件A'},{record_id:'B',role:'条件B'}],target_id:'target',statement:'条件表达',rationale:'渲染测试',evidence:[],unavailable_ids:[]}));

async function graphFixture(page) {
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.addInitScript(()=>localStorage.setItem('rw.active_project','motion'));
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:'motion',projects:[{id:'motion',name:'动画测试'}],sessions:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  await page.route('**/api/v1/projects/*/workspace',r=>r.fulfill({json:{status:'ready',url:'/lab'}}));
  await page.route('**/api/v1/projects/*/local-map',r=>r.fulfill({json:{records,relations,joint_conditions,artifacts:[],
    project_summary:{project_id:'motion',records:3},selection:{mode:'overview',matched_records:3,returned_records:3,truncated:false}}}));
  await page.goto('/map');
  await expect(page.locator('.joint-node')).toHaveCount(3);
  await expect(page.locator('.signal-flow-path')).toHaveCount(12);
}

function bubbleAppearance(node) {
  let opacity=1;
  for(let parent=node;parent;parent=parent.parentElement) {
    const style=getComputedStyle(parent);
    if(style.display==='none'||style.visibility==='hidden') return {visible:false};
    opacity*=Number(style.opacity);
  }
  const style=getComputedStyle(node), dashes=style.strokeDasharray.split(/[ ,]+/).map(parseFloat);
  return {visible:opacity>0 && style.stroke!=='none' && parseFloat(style.strokeWidth)>0 && node.getTotalLength()>0
    && style.strokeLinecap==='round' && dashes.length>=2 && dashes[1]>0,
    color:style.stroke,edgeColor:getComputedStyle(node.parentElement.querySelector('.react-flow__edge-path')).stroke};
}

async function expectMovingBubble(path) {
  const appearance=await path.evaluate(bubbleAppearance);
  expect(appearance.visible,`气泡不可见：${path}`).toBeTruthy();
  expect(appearance.color,`气泡与边的语义颜色不一致：${path}`).toBe(appearance.edgeColor);
  const offset=()=>path.evaluate(node=>getComputedStyle(node).strokeDashoffset);
  const before=await offset();
  await expect.poll(offset,{message:'气泡必须沿边移动，不能只保留静态路径',timeout:3000}).not.toBe(before);
}

test.use({screenshot:'only-on-failure'});

test('graph bubbles stay visible and moving on ordinary and joint edges',{tag:'@graph-motion'},async({page})=>{
  await graphFixture(page);
  for(const type of ['supports','refutes','depends_on','joint']) await expectMovingBubble(page.locator(`.polarity-${type} .signal-flow-path`).first());
  for(const rule of ['AND','OR','k-of-N']) {
    await page.locator('.joint-node').filter({hasText:`${rule==='k-of-N'?'1 / 2':rule}`}).first().click();
    const selected=page.locator('.polarity-joint.incident .signal-flow-path');
    await expect(selected).toHaveCount(3);
    for(const path of await selected.all()) await expectMovingBubble(path);
    for(const type of ['supports','refutes','depends_on','joint']) await expectMovingBubble(page.locator(`.polarity-${type}.muted .signal-flow-path`).first());
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  for(const path of await page.locator('.signal-flow-path').all()) await expect.poll(()=>path.evaluate(node=>getComputedStyle(node).display)).toBe('none');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await expectMovingBubble(page.locator('.polarity-joint .signal-flow-path').first());
});

test('dragging a record moves connected routes and preserves bubble colors',async({page})=>{
  await graphFixture(page);
  const node=page.locator('.react-flow__node').filter({has:page.locator('.research-node')}).first();
  const before=await node.getAttribute('style');
  const paths=()=>page.locator('.signal-flow-path').evaluateAll(ns=>ns.map(n=>n.getAttribute('d')));
  const routes=await paths(),box=await node.boundingBox();
  await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
  await page.mouse.down();await page.mouse.move(box.x+box.width/2+60,box.y+box.height/2+45,{steps:15});await page.mouse.up();
  await expect(node).not.toHaveAttribute('style',before);
  await expect.poll(paths).not.toEqual(routes);
  for(const type of ['supports','refutes','depends_on','joint'])await expectMovingBubble(page.locator(`.polarity-${type} .signal-flow-path`).first());
});
