'use client';
import React, { useEffect, useMemo, useState } from 'react';
import { supabase } from '../lib/supabase';
import StatusCards from '../components/StatusCards';
import Heatmap from '../components/Heatmap';
import Graph from '../components/Graph';
import Filters, { FilterState } from '../components/Filters';
import Artifacts from '../components/Artifacts';
import ThemeHeatmap from '../components/ThemeHeatmap';
import Throughput from '../components/Throughput';

type Run = { id:string; day:number; ok:boolean|null; started_at:string|null; finished_at:string|null; artifacts:any };
type Vot = { day:number; role:string|null; theme:string|null; };

export default function Page(){
  const [runs, setRuns] = useState<Run[]>([]);
  const [vots, setVots] = useState<Vot[]>([]);
  const [edges, setEdges] = useState<{src:number; dst:number;}[]>([]);
  const [filter, setFilter] = useState<FilterState>({ role:'', theme:'' });

  useEffect(()=>{
    const fetchAll = async()=>{
      const { data: runData } = await supabase.from('run').select('id, day, ok, started_at, finished_at, artifacts').limit(1000);
      setRuns(runData || []);

      // Optional VOT metadata for filters
      const { data: votData } = await supabase.from('vot').select('day, role, theme').limit(1000);
      setVots(votData || []);

      // Optional edge table (DAG)
      const { data: edgeData } = await supabase.from('edge').select('src, dst');
      setEdges(edgeData || []);
    };
    fetchAll();

    const ch = supabase.channel('runs')
      .on('postgres_changes', { event: '*', schema:'public', table:'run' }, ()=>{
        supabase.from('run').select('id, day, ok, started_at, finished_at, artifacts').then(({data})=>setRuns(data || []));
      }).subscribe();
    return ()=>{ supabase.removeChannel(ch); };
  }, []);

  const total = 365;
  const done = runs.filter(r=>r.ok === true).length;
  const open = total - done;

  // Compute filters
  const roles = useMemo(()=>Array.from(new Set(vots.map(v=>v.role).filter(Boolean))) as string[], [vots]);
  const themes = useMemo(()=>Array.from(new Set(vots.map(v=>v.theme).filter(Boolean))) as string[], [vots]);

  const includedDays = useMemo(()=>{
    let set = new Set<number>(Array.from({length:365}, (_,i)=>i+1));
    if (filter.role){
      const days = vots.filter(v=>v.role===filter.role).map(v=>v.day);
      set = new Set(days);
    }
    if (filter.theme){
      const themed = vots.filter(v=>v.theme===filter.theme).map(v=>v.day);
      set = new Set([...set].filter(d=>themed.includes(d)));
    }
    return set;
  }, [filter, vots]);

  const filteredRuns = useMemo(()=>runs.filter(r=>includedDays.has(r.day)), [runs, includedDays]);

  return (
    <main style={{padding:24, fontFamily:'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial'}}>
      <h1>QIL – Live Dashboard</h1>
      <p style={{opacity:.7, marginTop:0}}>Status, filters, DAG, and artifacts (read-only)</p>
      <StatusCards total={total} done={done} open={open} />
      <Filters roles={roles} themes={themes} value={filter} onChange={setFilter} />
      <div style={{display:'grid', gridTemplateColumns:'1fr', gap:24, marginTop:24}}>
        <Heatmap items={filteredRuns.map(r=>({day:r.day, ok:r.ok}))} include={includedDays}/>
        <Graph edges={edges} runs={filteredRuns} />
        <ThemeHeatmap rows={filteredRuns.map(r=>({day:r.day, theme:(vots.find(v=>v.day===r.day)?.theme || null), ok:r.ok}))} />
        <Throughput runs={filteredRuns} />
        <Artifacts runs={filteredRuns} />
      </div>
    </main>
  );
}
