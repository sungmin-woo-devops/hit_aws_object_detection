import React, { useState } from 'react';
import { api, setToken, getToken } from './api/client';

export default function App() {
  const [email, setEmail] = useState('');
  const [pw, setPw] = useState('');
  const [msg, setMsg] = useState('');
  const [me, setMe] = useState(null);

  async function signup(e) {
    e.preventDefault();
    try { await api('/auth/signup', { method:'POST', body:{ email, password: pw } });
      setMsg('회원가입 완료'); } catch (e) { setMsg(e.message); }
  }
  async function login(e) {
    e.preventDefault();
    try {
      const form = new URLSearchParams({ username: email, password: pw });
      const r = await fetch('/auth/login', {
        method:'POST',
        headers:{ 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString()
      });
      if (!r.ok) throw new Error((await r.json()).detail || '로그인 실패');
      const data = await r.json();
      setToken(data.access_token);
      setMsg('로그인 성공');
    } catch (e) { setMsg(e.message); }
  }
  async function fetchMe() {
    try { setMe(await api('/me')); setMsg(''); } catch(e){ setMsg(e.message); }
  }
  function logout(){ setToken(null); setMe(null); setMsg('로그아웃'); }

  return (
    <div style={{maxWidth:420,margin:'40px auto',fontFamily:'ui-sans-serif'}}>
      <h2>Auth Demo (React + Vite)</h2>
      <form onSubmit={signup} style={{marginBottom:8}}>
        <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)}
               style={{width:'100%',padding:8,marginBottom:8}} />
        <input type="password" placeholder="password" value={pw} onChange={e=>setPw(e.target.value)}
               style={{width:'100%',padding:8,marginBottom:8}} />
        <button type="submit" style={{width:'100%',padding:8}}>회원가입</button>
      </form>
      <form onSubmit={login} style={{marginBottom:8}}>
        <button type="submit" style={{width:'100%',padding:8}}>로그인</button>
      </form>
      <div style={{display:'flex',gap:8}}>
        <button onClick={fetchMe} style={{flex:1,padding:8}}>내 정보</button>
        <button onClick={logout} style={{flex:1,padding:8}}>로그아웃</button>
      </div>
      <p style={{marginTop:8,opacity:.8}}>토큰: {getToken() ? '있음' : '없음'}</p>
      {msg && <p style={{marginTop:8}}>{msg}</p>}
      {me && <pre style={{background:'#f5f5f5',padding:12,marginTop:12}}>{JSON.stringify(me,null,2)}</pre>}
    </div>
  );
}
