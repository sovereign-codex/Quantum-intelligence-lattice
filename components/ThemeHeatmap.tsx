'use client';
import React, { useMemo } from 'react';

type Row = { day:number; theme:string|null; ok:boolean|null; };

export default function ThemeHeatmap({ rows }: { rows: Row[] }){
  const byTheme = useMemo(()=>{
    const map = new Map<string, {done:number; total:number}>();
    rows.forEach(r=>{
      const key = r.theme || 'Unknown';
      if(!map.has(key)) map.set(key, {done:0, total:0});
      const obj = map.get(key)!;
      obj.total += 1;
      if (r.ok === true) obj.done += 1;
    });
    return Array.from(map.entries());
  }, [rows]);

  return (
    <div style={{marginTop:24}}>
      <h3>Theme Completion</h3>
      <div style={{display:'grid', gap:8}}>
        {byTheme.map(([theme, vals])=>{
          const pct = vals.total ? Math.round((vals.done/vals.total)*100) : 0;
          return (
            <div key={theme}>
              <div style={{fontSize:12, marginBottom:4}}>{theme} — {pct}%</div>
              <div style={{height:10, background:'#eee', borderRadius:4, overflow:'hidden'}}>
                <div style={{width:`${pct}%`, height:'100%'}} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
