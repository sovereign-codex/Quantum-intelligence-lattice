'use client';
import React from 'react';

export type FilterState = {
  role: string;
  theme: string;
};

export default function Filters({
  roles, themes, value, onChange
}: {
  roles: string[];
  themes: string[];
  value: FilterState;
  onChange: (v: FilterState)=>void;
}){
  return (
    <div style={{display:'flex', gap:12, alignItems:'center', marginTop:16}}>
      <label style={{display:'flex', flexDirection:'column', fontSize:12}}>
        Role
        <select
          value={value.role}
          onChange={e=>onChange({...value, role: e.target.value})}
          style={{padding:6, border:'1px solid #ddd', borderRadius:6}}
        >
          <option value="">All</option>
          {roles.map(r=>(<option key={r} value={r}>{r}</option>))}
        </select>
      </label>
      <label style={{display:'flex', flexDirection:'column', fontSize:12}}>
        Theme
        <select
          value={value.theme}
          onChange={e=>onChange({...value, theme: e.target.value})}
          style={{padding:6, border:'1px solid #ddd', borderRadius:6}}
        >
          <option value="">All</option>
          {themes.map(t=>(<option key={t} value={t}>{t}</option>))}
        </select>
      </label>
    </div>
  );
}
