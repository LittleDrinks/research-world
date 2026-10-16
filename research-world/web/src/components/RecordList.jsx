import {useNavigate} from 'react-router-dom';
import {useWorld} from '../context/WorldContext';

export function RecordList({module,close}) {
  const {data}=useWorld(),navigate=useNavigate();
  const values=module==='/chat'||module==='/traces'?data.sessions:module==='/agents'?data.agents:[];
  return <section className="record-list"><div className="record-items">{values.map(value=><button className="record-item" key={value.id} onClick={()=>{navigate(`${module}/${value.id}`);close();}}><span>{value.title||value.name}</span></button>)}</div></section>;
}
