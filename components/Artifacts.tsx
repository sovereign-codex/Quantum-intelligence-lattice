'use client';
import React from 'react';

type Run = { id:string; day:number; ok:boolean|null; started_at:string|null; finished_at:string|null; artifacts: any };

export default function Artifacts({ runs }: { runs: Run[] }){
  return (
    <div style={{marginTop:24}}>
      <h3>Artifacts</h3>
      <div style={{fontSize:12, opacity:.7, marginBottom:8}}>Listing the latest 50 runs that have artifacts</div>
      <div style={{display:'grid', gap:12}}>
        {runs
          .filter(r=>r.artifacts && Object.keys(r.artifacts).length > 0)
          .slice(0,50)
          .map(r=>(
          <div key={r.id} style={{border:'1px solid #eee', borderRadius:8, padding:12}}>
            <div style={{fontWeight:600}}>Day {r.day} {r.ok===true ? '✅' : (r.ok===false ? '⚠️' : '')}</div>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(r.artifacts, null, 2)}</pre>
            <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
              {Object.values(r.artifacts).map((val, i)=>{
                if (typeof val === 'string' && (val.startsWith('http://') || val.startsWith('https://'))) {
                  return <a key={i} href={val} target="_blank" style={{fontSize:12, textDecoration:'underline'}}>Open link</a>;
                }
                return null;
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
