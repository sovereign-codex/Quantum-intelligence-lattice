'use client';
import React, { useEffect, useRef } from 'react';
import cytoscape, { ElementDefinition } from 'cytoscape';

type Edge = { src:number; dst:number; };
type Run = { day:number; ok:boolean|null; };

export default function Graph({ edges, runs }: { edges: Edge[]; runs: Run[] }){
  const ref = useRef<HTMLDivElement>(null);

  useEffect(()=>{
    if(!ref.current) return;
    const runMap = new Map(runs.map(r=>[r.day, r.ok]));
    const nodes: ElementDefinition[] = Array.from({length:365}, (_,i)=>({
      data:{ id:`n${i+1}`, label:`${i+1}`},
      classes: runMap.get(i+1) ? 'ok' : 'open'
    }));
    const es: ElementDefinition[] = edges.map(e=>({ data:{ id:`e${e.src}_${e.dst}`, source:`n${e.src}`, target:`n${e.dst}` }}));
    const cy = cytoscape({
      container: ref.current,
      elements: [...nodes, ...es],
      layout: { name:'cose', animate:false },
      style: [
        { selector:'node', style:{ 'label':'data(label)', 'font-size':6, 'width':6, 'height':6, 'background-color':'#999' } },
        { selector:'node.ok', style:{ 'background-color':'#4caf50' } },
        { selector:'node.open', style:{ 'background-color':'#bbb' } },
        { selector:'edge', style:{ 'width':1, 'line-color':'#ddd', 'target-arrow-color':'#ddd', 'target-arrow-shape':'triangle', 'curve-style':'bezier' } }
      ]
    });
    return ()=>{ cy.destroy(); };
  }, [edges, runs]);

  return <div style={{height:480, border:'1px solid #eee', borderRadius:8}} ref={ref}/>;
}
