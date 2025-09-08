'use client';
import React, { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, LineElement, LinearScale, PointElement, CategoryScale, Tooltip, Legend } from 'chart.js';
ChartJS.register(LineElement, LinearScale, PointElement, CategoryScale, Tooltip, Legend);

type Run = { day:number; ok:boolean|null; };

export default function Throughput({ runs }: { runs: Run[] }){
  const data = useMemo(()=>{
    // naive: cumulative done over 365
    const arr = new Array(365).fill(0);
    runs.forEach(r=>{
      if (r.ok === true && r.day >=1 && r.day <= 365) arr[r.day-1] = 1;
    });
    let cum = 0;
    const cumArr = arr.map(v=>cum += v);
    return {
      labels: Array.from({length:365}, (_,i)=>i+1),
      datasets: [{
        label: 'Cumulative Done',
        data: cumArr
      }]
    };
  }, [runs]);

  const options = useMemo(()=>({ responsive:true, plugins:{ legend:{ display:true }}, scales:{ x:{ title:{ display:true, text:'Day' }}, y:{ title:{ display:true, text:'Completed' }, beginAtZero:true }}}), []);

  return (
    <div style={{marginTop:24}}>
      <h3>Throughput (Cumulative)</h3>
      <Line data={data} options={options} />
    </div>
  );
}
