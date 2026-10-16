export function filePath(path){
  const segments=path.split('/');
  if(!path||segments.some(part=>!part||part==='.'||part==='..')||/[\\\u0000-\u001f]/.test(path))throw Error('工作区文件路径无效');
  return segments.map(encodeURIComponent).join('/');
}

export function workspaceFileLink(href,projectId){
  if(!href||!projectId)return href;
  try{
    const url=new URL(href,window.location.origin);
    if(url.origin!==window.location.origin||!url.pathname.startsWith('/workspace/'))return href;
    const path=filePath(decodeURIComponent(url.pathname.slice('/workspace/'.length)));
    return `/workspace/${path}?project=${encodeURIComponent(projectId)}`;
  }catch{return href;}
}

export function editorUrl(workspaceUrl,path){
  const url=new URL(workspaceUrl);
  url.pathname=`${url.pathname.replace(/\/$/,'')}/tree/${filePath(path)}`;
  return url.href;
}
