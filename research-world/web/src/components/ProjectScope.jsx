import {useEffect,useState} from 'react';
import {useParams} from 'react-router-dom';
import {useWorld} from '../context/WorldContext';

export function ProjectScope({children}){
  const {projectId:target}=useParams(),{projectId,loading,selectProject}=useWorld(),[error,setError]=useState('');
  useEffect(()=>{if(!loading&&projectId!==target&&!error)selectProject(target).catch(e=>setError(e.message));},[target,projectId,loading,error]);
  if(error)return <p role="alert">{error}</p>;
  return !loading&&projectId===target?children:<p role="status">正在打开研究项目…</p>;
}
