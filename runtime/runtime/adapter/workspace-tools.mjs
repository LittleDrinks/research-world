import {createReadToolDefinition,createWriteToolDefinition,createEditToolDefinition,createBashToolDefinition} from '@earendil-works/pi-coding-agent';
import {readFile,unlink} from 'node:fs/promises';
import {basename} from 'node:path';

async function remote(values,signal,onData){
  const response=await fetch('http://127.0.0.1:8098/internal/workspace',{
    method:'POST',signal,headers:{'Content-Type':'application/json','X-Tool-Token':process.env.RW_TOOL_TOKEN},body:JSON.stringify(values),
  });
  if(!response.ok)throw new Error(`Workspace operation failed (${response.status})`);
  let pending='',result={};
  for await(const chunk of response.body.pipeThrough(new TextDecoderStream())){
    pending+=chunk;
    while(pending.includes('\n')){
      const index=pending.indexOf('\n'),event=JSON.parse(pending.slice(0,index));pending=pending.slice(index+1);
      if(event.data)onData(Buffer.from(event.data,'base64'));
      else result={...result,...event};
    }
  }
  if(result.error)throw new Error(result.error);
  if(result.exitCode===undefined)throw new Error('Workspace stream ended without a result');
  return result;
}

async function file(operation,path,signal,content){
  const chunks=[];
  const result=await remote({operation,path,...(content===undefined?{}:{content})},signal,data=>chunks.push(data));
  const output=Buffer.concat(chunks);
  if(result.exitCode!==0)throw new Error(output.toString()||'Workspace file operation failed');
  return output;
}

function operations(signal){
  return {
    readFile:path=>file('read',path,signal),
    writeFile:(path,content)=>file('write',path,signal,content),
    access:path=>file('access',path,signal),
    mkdir:path=>file('mkdir',path,signal),
    detectImageMimeType:async path=>{const mime=(await file('mime',path,signal)).toString().trim();return mime.startsWith('image/')?mime:null;},
    exec:(command,_cwd,options)=>remote({operation:'bash',command,timeout:options.timeout??120},options.signal,options.onData),
  };
}

async function workspaceOutput(result,signal){
  const path=result.details?.fullOutputPath;
  if(!path)return result;
  const target=`/workspace/.outputs/${basename(path)}`;
  await file('mkdir','/workspace/.outputs',signal);
  await file('write',target,signal,await readFile(path,'utf8'));
  await unlink(path);
  return JSON.parse(JSON.stringify(result).replaceAll(path,target));
}

export function registerWorkspaceTools(pi){
  for(const factory of [createReadToolDefinition,createWriteToolDefinition,createEditToolDefinition,createBashToolDefinition]){
    const base=factory('/workspace',{exposeSessionEnvironment:false,operations:operations()});
    pi.registerTool({...base,description:`${base.description} Operates in the current Project container at /workspace, shared with JupyterLab.`,
      async execute(id,args,signal,onUpdate,ctx){
        const tool=factory('/workspace',{exposeSessionEnvironment:false,operations:operations(signal)});
        const update=value=>onUpdate?.({...value,details:{...value.details,fullOutputPath:undefined}});
        const result=await tool.execute(id,args,signal,update,{...ctx,cwd:'/workspace'});
        return workspaceOutput(result,signal);
      },
    });
  }
}
