import {test,expect} from '@playwright/test';

const project='project:'+'a'.repeat(24),other='project:'+'b'.repeat(24);
async function fixture(page){
  await page.routeWebSocket('**/workspace/presence',socket=>socket.send(JSON.stringify({status:'ready',url:'/lab?token=synthetic-test'})));
  await page.route('**/api/v1/bootstrap**',r=>r.fulfill({json:{active_project_id:other,projects:[{id:other,name:'当前项目'},{id:project,name:'文件所属项目'}],sessions:[],nodes:[],edges:[]}}));
  await page.route('**/api/v1/agents',r=>r.fulfill({json:[]}));
  await page.route('**/lab/tree/**',r=>r.fulfill({contentType:'text/html; charset=utf-8',body:'<h1>文件编辑器</h1>'}));
}

function ready(page){return {status:'ready',url:new URL('/lab?token=synthetic-test',page.url()).href};}

for(const explicit of [false,true])test(`workspace file opens using ${explicit?'bound':'active'} project`,async({page})=>{
  await fixture(page);const calls=[];
  await page.route('**/api/v1/projects/*/workspace',r=>{calls.push(decodeURIComponent(r.request().url()));return r.fulfill({json:ready(page)});});
  await page.goto('/workspace/add.py'+(explicit?`?project=${project}`:''));
  await expect(page.getByRole('heading',{name:'文件编辑器'})).toBeVisible();
  expect(new URL(page.url()).pathname).toBe('/lab/tree/add.py');
  expect(calls.every(url=>url.includes(explicit?project:other))).toBeTruthy();
});

for(const filename of ['中文 a+#.py','literal%2Fname.py','literal%252Fname.py'])test(`stopped workspace opens ${filename}`,async({page})=>{
  await fixture(page);const methods=[];
  await page.route('**/api/v1/projects/*/workspace',r=>{methods.push(r.request().method());return r.fulfill({json:r.request().method()==='POST'?ready(page):{status:'exited'}});});
  await page.goto('/workspace/'+encodeURIComponent(filename));
  await expect(page.getByRole('heading',{name:'文件编辑器'})).toBeVisible();
  expect(decodeURIComponent(new URL(page.url()).pathname)).toBe('/lab/tree/'+filename);
  expect(methods).toContain('POST');
});

test('workspace failure is shown without navigating away',async({page})=>{
  await fixture(page);
  await page.route('**/api/v1/projects/*/workspace',r=>r.fulfill({status:503,json:{detail:'容器服务不可用'}}));
  await page.goto('/workspace/add.py');
  await expect(page.getByRole('alert')).toHaveText('容器服务不可用');
  expect(new URL(page.url()).pathname).toBe('/workspace/add.py');
});

test('chat file links bind the message project and leave other links alone',async({page})=>{
  await fixture(page);
  const answer='[add.py](/workspace/add.py) [来源](https://example.org/workspace/paper) [产物](/api/v1/projects/x/artifacts/y)';
  await page.route('**/sessions/s-links',r=>r.fulfill({json:{session:{project_id:project,title:'文件',messages:[{id:'m',content:'创建脚本',assistant_response:answer}]},run:{turns:[{id:'t',message_id:'m',status:'completed',events:[]}]}}}));
  await page.goto('/chat/s-links');
  await expect(page.getByRole('link',{name:'add.py',exact:true})).toHaveAttribute('href',`/workspace/add.py?project=${encodeURIComponent(project)}`);
  await expect(page.getByRole('link',{name:'来源',exact:true})).toHaveAttribute('href','https://example.org/workspace/paper');
  await expect(page.getByRole('link',{name:'产物',exact:true})).toHaveAttribute('href','/api/v1/projects/x/artifacts/y');
});


test('same-site server workspace URL opens its project editor',async({page})=>{
  await fixture(page);
  await page.route('**/api/v1/projects/*/workspace',r=>r.fulfill({json:{status:'ready',url:'/labs/'+project.slice(8)+'/lab?token=synthetic-test'}}));
  await page.goto('/workspace/add.py?project='+project);
  await expect(page.getByRole('heading',{name:'文件编辑器'})).toBeVisible();
  expect(new URL(page.url()).pathname).toBe('/labs/'+project.slice(8)+'/lab/tree/add.py');
});
