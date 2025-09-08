'use client';
import React from 'react';

export default function StatusCards({ total, done, open }: { total:number; done:number; open:number }){
  const inProgress = total - done - open >= 0 ? total - done - open : 0;
  return (
    <div style={{display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:16, marginTop:16}}>
      <div style={{border:'1px solid #ddd', borderRadius:8, padding:16}}>
        <div style={{fontSize:12, opacity:.7}}>TOTAL VOTs</div>
        <div style={{fontSize:28, fontWeight:700}}>{total}</div>
      </div>
      <div style={{border:'1px solid #ddd', borderRadius:8, padding:16}}>
        <div style={{fontSize:12, opacity:.7}}>DONE</div>
        <div style={{fontSize:28, fontWeight:700}}>{done}</div>
      </div>
      <div style={{border:'1px solid #ddd', borderRadius:8, padding:16}}>
        <div style={{fontSize:12, opacity:.7}}>OPEN</div>
        <div style={{fontSize:28, fontWeight:700}}>{open}</div>
      </div>
    </div>
  );
}
