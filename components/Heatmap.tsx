'use client';
import React, { useMemo } from 'react';

type Item = { day:number; ok:boolean|null; };

export default function Heatmap({ items, include }: { items: Item[]; include?: Set<number> }){
  const cells = useMemo(()=>{
    const arr = new Array(365).fill(null).map((_,i)=>items.find(it=>it.day===i+1));
    return arr;
  }, [items]);

  const isIncluded = (idx:number)=> !include || include.has(idx+1);

  return (
    <div>
      <div style={{margin:'16px 0', fontWeight:600}}>Year Heatmap</div>
      <div style={{
        display:'grid',
        gridTemplateColumns:'repeat(73, 10px)',
        gap:'2px'
      }}>
        {cells.map((it, idx)=>{
          let bg = '#eee';
          if (!isIncluded(idx)) bg = '#f0f0f0';
          else if (it?.ok === true) bg = '#88e28b';
          else if (it?.ok === false) bg = '#f5b7b1';
          return <div key={idx} title={`Day ${idx+1}`} style={{width:10, height:10, background:bg, borderRadius:2}}/>;
        })}
      </div>
    </div>
  );
}
