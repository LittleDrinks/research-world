import {request} from 'undici';

export async function requestTool(name, args, signal) {
  const response = await request('http://127.0.0.1:8098/internal/tools', {
    method: 'POST', signal, headersTimeout: 0, bodyTimeout: 0,
    headers: {'Content-Type': 'application/json', 'X-Tool-Token': process.env.RW_TOOL_TOKEN},
    body: JSON.stringify({tool: name, arguments: args}),
  });
  if (response.statusCode < 200 || response.statusCode >= 300) {
    if(name==='artifact'&&response.statusCode===422){
      const body=await response.body.json();
      throw new Error(JSON.stringify(body.detail));
    }
    await response.body.dump();
    throw new Error(`Tool failed (${response.statusCode})`);
  }
  return response.body.json();
}
