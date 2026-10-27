"""Monta a página do painel a partir de dados/leads_detalhados_*.csv (usada por server.py)."""
import csv
import json
from pathlib import Path

from comum import DADOS, ler_meta

BASE = Path(__file__).parent
SAIDA = BASE / "saida" / "pagina_leads.html"

# __LEADS__ é substituído pelo JSON dos leads
HTML = r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Painel de leads</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#EDEFEC;--pn:#FFFFFF;--sb:#F7F8F6;--ink:#1C242B;--mut:#5B6770;--bd:#D9DDD8;--bd2:#E8EAE6;
    --ac:#0E6F5C;--acbg:#DDEFEA;--warn:#9A5B00;--warnbg:#F7E8CC;--bad:#A93226;--badbg:#F6DDD9;
    --dial:#1C242B;--dialtx:#F2F4F1;--dialmut:#9AA6AF;--dialtrk:#33404A;
    --disp:"Bricolage Grotesque","Segoe UI",system-ui,sans-serif;
    --txt:"Public Sans","Segoe UI",system-ui,sans-serif;
    --sbw:360px;
  }
  @media (prefers-color-scheme:dark){:root{
    --bg:#12171B;--pn:#1A2127;--sb:#161C21;--ink:#E6EAE7;--mut:#9AA6AF;--bd:#2B343B;--bd2:#232B31;
    --ac:#4CC3A4;--acbg:#173129;--warn:#F0B954;--warnbg:#38301A;--bad:#F2877D;--badbg:#3A1E1B;
    --dial:#0C1013;--dialtrk:#27313A}}
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--txt);display:grid;grid-template-columns:64px var(--sbw) 1fr;overflow:hidden}
  button,input,select,textarea{font:inherit;color:inherit}
  button{cursor:pointer}
  :focus-visible{outline:2px solid var(--ac);outline-offset:2px}
  a{color:var(--ac)}
  .num{font-family:var(--disp);font-variant-numeric:tabular-nums}

  /* ---------- barra lateral ---------- */
  #nav{background:var(--dial);display:flex;flex-direction:column;align-items:center;gap:6px;padding:12px 0}
  #nav button{width:52px;border:0;background:none;color:var(--dialmut);border-radius:8px;padding:8px 0 6px;cursor:pointer;font:600 11px var(--txt);display:flex;flex-direction:column;align-items:center;gap:4px}
  #nav button:hover{color:var(--dialtx)}
  #nav button[aria-current="page"]{background:var(--dialtrk);color:var(--dialtx)}
  #nav svg{width:22px;height:22px;flex:none}
  #nav .tg{margin-bottom:6px}
  #nav .tg svg{transition:transform .2s}
  body.nav-open{grid-template-columns:190px var(--sbw) 1fr}
  body.nav-open #nav{align-items:stretch;padding:12px 10px}
  body.nav-open #nav button{width:auto;flex-direction:row;gap:10px;padding:10px 12px;font-size:14px}
  body.nav-open #nav .tg svg{transform:rotate(180deg)}
  #kanban{grid-column:2/4;display:none;flex-direction:column;min-width:0;min-height:0}
  body.crm #sb,body.crm #main,body.wpp #sb,body.wpp #main,body.fila #sb,body.fila #main{display:none}
  #fila{grid-column:2/4;display:none;flex-direction:column;min-width:0;overflow:auto}
  body.fila #fila{display:flex}
  .fl-cfg{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:12px 0}
  .fl-cfg label{font-size:12px;color:var(--mut);display:flex;flex-direction:column;gap:3px}
  .fl-wrap{margin:0 20px 24px;max-width:980px}
  .fl-row{display:grid;grid-template-columns:1fr auto;gap:4px 12px;padding:10px 12px;background:var(--pn);border:1px solid var(--bd);border-radius:8px;margin-bottom:6px;font-size:13px}
  .fl-row b{font-size:14px}.fl-row .tx{grid-column:1/3;color:var(--mut);white-space:pre-wrap;max-height:3.2em;overflow:hidden}
  .fl-st{font-weight:600;font-size:12px;padding:1px 8px;border-radius:4px;background:var(--bd2);color:var(--mut)}
  .fl-st.aprovada{background:var(--acbg);color:var(--ac)}.fl-st.enviada{background:var(--ac);color:var(--pn)}.fl-st.erro,.fl-st.sem_whatsapp{background:var(--badbg);color:var(--bad)}
  body.crm #kanban{display:flex}
  #wpp{grid-column:2/4;display:none;flex-direction:column;min-width:0;overflow:auto}
  body.wpp #wpp{display:flex}
  .wp-box{max-width:520px;margin:24px 20px;padding:20px;background:var(--pn);border:1px solid var(--bd);border-radius:10px}
  .wp-st{display:flex;align-items:center;gap:10px;font:700 18px var(--disp);margin:0 0 6px}
  .wp-st i{width:12px;height:12px;border-radius:50%;background:var(--mut)}
  .wp-st.open i{background:#22c55e}.wp-st.connecting i{background:#f59e0b}.wp-st.off i{background:#ef4444}
  .wp-box p{color:var(--mut);font-size:14px;margin:6px 0}
  #wp-qr{display:block;width:260px;height:260px;margin:14px 0;background:#fff;padding:8px;border-radius:8px}
  #wp-err{color:var(--bad);font-size:13px;min-height:1em;margin-top:8px}
  .kb-top{padding:18px 20px 12px;border-bottom:1px solid var(--bd);background:var(--sb)}
  .kb-top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
  .kb-top h1{font:700 22px var(--disp);margin:0}.kb-top p{margin:2px 0 0;color:var(--mut);font-size:13px}
  .kb-board{flex:1;display:flex;gap:12px;padding:16px 20px;overflow:auto;align-items:flex-start}
  .kb-col{flex:0 0 250px;background:var(--sb);border:1px solid var(--bd);border-radius:10px;display:flex;flex-direction:column;max-height:100%}
  .kb-col{border-top:4px solid var(--c);background:color-mix(in srgb,var(--c) 7%,var(--sb))}
  .kb-col.over{border-color:var(--c);background:color-mix(in srgb,var(--c) 22%,var(--sb))}
  .kb-col h2 i{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--c);margin-right:7px}
  .kb-col h2 label{display:inline-flex;align-items:center;cursor:pointer;margin-left:8px}
  .kb-col input[type=color]{width:20px;height:20px;padding:0;border:1px solid var(--bd);border-radius:4px;background:none;cursor:pointer}
  .kb-col h2 .cnt{background:var(--c);color:#fff;border-radius:10px;padding:0 8px;font:600 12px/20px var(--txt);min-width:22px;height:20px;text-align:center;align-self:center}
  .kb-col h2 .kb-tt{display:flex;align-items:center;gap:4px;color:var(--ink);font:700 14px var(--disp);min-width:0;flex-wrap:wrap}
  .kb-col h2[draggable]{cursor:grab}
  .kb-ic{border:0;background:none;color:var(--mut);cursor:pointer;padding:0 3px;font-size:13px;line-height:1;border-radius:4px;opacity:.55}
  .kb-ic:hover{opacity:1;color:var(--ink)}
  .kb-col.ins-antes{box-shadow:-5px 0 0 0 var(--c)}.kb-col.ins-depois{box-shadow:5px 0 0 0 var(--c)}
  .kb-add{flex:0 0 220px;align-self:flex-start;border:2px dashed var(--bd);background:none;color:var(--mut);border-radius:10px;padding:14px;cursor:pointer;font:600 14px var(--txt);display:flex;align-items:center;justify-content:center;gap:8px}
  .kb-add::first-letter{font-size:20px}
  .kb-add:hover{border-color:var(--ac);color:var(--ac)}
  .kb-col h2{font:700 14px var(--disp);margin:0;padding:12px 12px 2px;display:flex;justify-content:space-between}
  .kb-col h2 span{color:var(--mut);font:500 13px var(--txt)}
  .kb-col .sub2{color:var(--mut);font-size:12px;padding:0 12px 8px}
  .kb-line{display:block;margin-top:6px;font-size:12px;color:var(--mut)}
  .kb-line.late{color:var(--bad);font-weight:600}
  #dlg-lead{width:min(760px,calc(100vw - 32px));max-height:88vh;overflow:auto}
  #dlg-lead h2{font:700 22px var(--disp);margin:0}
  #dlg-lead .hd{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
  #dlg-lead h3{font:700 15px var(--disp);margin:20px 0 8px}
  #dlg-lead dl{display:grid;grid-template-columns:110px 1fr;gap:4px 12px;margin:0;font-size:14px}
  #dlg-lead dt{color:var(--mut)}#dlg-lead dd{margin:0}
  .tl{list-style:none;margin:0;padding:0 0 0 14px;border-left:2px solid var(--bd)}
  .tl li{position:relative;margin-bottom:14px}
  .tl li::before{content:"";position:absolute;left:-20px;top:5px;width:10px;height:10px;border-radius:50%;background:var(--ac)}
  .tl .when{color:var(--mut);font-size:12px}
  .quote{margin:6px 0 0;padding:8px 10px;background:var(--sb);border:1px solid var(--bd2);border-radius:6px;white-space:pre-wrap;font-size:13px}
  #dlg-lead textarea{width:100%;min-height:70px}
  .kb-cards{padding:0 8px 8px;overflow:auto;min-height:40px;display:flex;flex-direction:column;gap:8px}
  .kb-card{background:var(--pn);border:1px solid var(--bd);border-radius:8px;padding:10px;cursor:grab;font-size:13px;text-align:left;color:var(--ink);font-family:inherit;width:100%}
  .kb-card{border-left:5px solid var(--c)}
  .kb-card:hover{border-color:var(--c)}
  .kb-card b{display:block;font-size:14px}
  .kb-card small{color:var(--mut);display:block;margin-top:2px}
  .kb-card .badge{margin-top:6px}
  .kb-empty{color:var(--mut);font-size:13px;padding:8px 4px}
  #sb{background:var(--sb);border-right:1px solid var(--bd);display:flex;flex-direction:column;min-height:0}
  .sb-top{padding:18px 18px 14px;border-bottom:1px solid var(--bd)}
  .sb-top h1{font:700 20px/1.1 var(--disp);margin:0 0 2px;letter-spacing:-.01em}
  .sb-top p{margin:0;color:var(--mut);font-size:13px}
  .dist{display:flex;height:6px;border-radius:3px;overflow:hidden;margin:14px 0 6px;background:var(--bd)}
  .dist i{display:block;height:100%}
  .dist .alta{background:var(--ac)}.dist .media{background:#D9962B}.dist .baixa{background:var(--bad)}
  .legend{display:flex;gap:14px;font-size:12px;color:var(--mut)}
  .legend b{font-family:var(--disp);color:var(--ink);font-weight:700}
  .find{padding:12px 18px;display:grid;gap:8px;border-bottom:1px solid var(--bd)}
  .field{width:100%;background:var(--pn);border:1px solid var(--bd);border-radius:6px;padding:8px 10px}
  .field:focus-visible{outline-offset:0}
  .two{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .niches{display:flex;flex-wrap:wrap;gap:6px}
  .nc{border:1px solid var(--bd);background:transparent;border-radius:14px;padding:3px 10px;font-size:13px;color:var(--mut)}
  .nc:hover{border-color:var(--ac);color:var(--ink)}
  .nc[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:var(--pn)}
  .nc span{font-family:var(--disp);margin-left:4px;opacity:.7}
  .count{padding:8px 18px;font-size:12px;color:var(--mut);border-bottom:1px solid var(--bd2)}
  #list{overflow:auto;flex:1;min-height:0}
  .row{display:grid;grid-template-columns:1fr auto;gap:2px 10px;width:100%;text-align:left;background:transparent;border:0;border-bottom:1px solid var(--bd2);border-left:3px solid transparent;padding:11px 18px 12px 15px;position:relative}
  .row:hover{background:var(--pn)}
  .row[aria-current=true]{background:var(--pn);border-left-color:var(--ink)}
  .row .nm{font-weight:600;line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .row .pc{font:700 18px/1.2 var(--disp);text-align:right}
  .row .sub{font-size:12.5px;color:var(--mut);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .row .meter{grid-column:1/-1;height:3px;background:var(--bd2);border-radius:2px;margin-top:6px;overflow:hidden}
  .row .meter i{display:block;height:100%}
  .alta{color:var(--ac)}.media{color:var(--warn)}.baixa{color:var(--bad)}
  .meter .alta{background:var(--ac)}.meter .media{background:#D9962B}.meter .baixa{background:var(--bad)}
  .empty{padding:28px 18px;color:var(--mut)}
  .empty b{display:block;color:var(--ink);margin-bottom:4px}

  /* ---------- ficha ---------- */
  #main{overflow:auto;min-width:0}
  .sheet{max-width:1040px;margin:0 auto;padding:28px 36px 64px}
  .back{display:none;border:1px solid var(--bd);background:var(--pn);border-radius:6px;padding:6px 12px;margin-bottom:14px}
  .head h2{font:700 30px/1.1 var(--disp);letter-spacing:-.02em;margin:0 0 6px}
  .head .addr{color:var(--mut);margin:0 0 10px;max-width:70ch}
  .badge{display:inline-block;border-radius:4px;padding:1px 8px;font-size:12px;font-weight:600;background:var(--bd2);color:var(--mut);margin-right:6px}
  .badge.cor{background:color-mix(in srgb,var(--c) 20%,var(--pn));color:color-mix(in srgb,var(--c) 65%,var(--ink));box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--c) 45%,transparent)}
  .st-renovar{background:var(--badbg);color:var(--bad)}
  .top{display:grid;grid-template-columns:260px 1fr;gap:28px;margin:22px 0 8px;align-items:stretch}
  .dial{align-self:start;background:var(--dial);color:var(--dialtx);border-radius:10px;padding:18px 18px 16px;text-align:center}
  .dial svg{width:100%;display:block}
  .dial .trk{stroke:var(--dialtrk)}
  .dial .val{transition:stroke-dashoffset .6s cubic-bezier(.2,.8,.2,1),stroke .3s}
  .dial .big{font:700 46px/1 var(--disp);margin-top:-52px;position:relative}
  .dial .of{font-size:12.5px;color:var(--dialmut);margin-top:8px}
  .prods{display:grid;gap:4px;align-content:start}
  .prod{display:grid;grid-template-columns:1fr auto;gap:0 12px;text-align:left;background:transparent;border:1px solid transparent;border-bottom-color:var(--bd);padding:9px 10px;border-radius:6px}
  .prod:hover{background:var(--pn)}
  .prod[aria-pressed=true]{background:var(--pn);border-color:var(--ink)}
  .prod b{font-weight:600}.prod .p{font:700 16px/1.2 var(--disp)}
  .prod .meter{grid-column:1/-1;height:3px;background:var(--bd2);border-radius:2px;margin-top:6px;overflow:hidden}
  .prod .meter i{display:block;height:100%}
  .star{font-size:12px;color:var(--mut);font-weight:400;margin-left:6px}
  .why{margin:10px 10px 0;padding:0;list-style:none;color:var(--mut);font-size:13.5px}
  .why li{padding:2px 0 2px 14px;position:relative}
  .why li::before{content:"";position:absolute;left:0;top:.75em;width:6px;height:2px;background:var(--bd)}

  .sec{display:grid;grid-template-columns:170px 1fr;gap:8px 28px;padding:24px 0;border-top:1px solid var(--bd)}
  .sec>h3{font:700 16px/1.3 var(--disp);margin:0}
  .sec>h3 small{display:block;font:400 13px/1.4 var(--txt);color:var(--mut);margin-top:4px}
  dl{display:grid;grid-template-columns:120px 1fr;gap:8px 16px;margin:0}
  dt{color:var(--mut)}dd{margin:0;word-break:break-word}
  .hrs{display:grid;grid-template-columns:auto 1fr;gap:2px 16px}
  .hrs span:nth-child(odd){color:var(--mut)}
  label{display:block;font-size:13px;color:var(--mut);margin:12px 0 4px}
  label:first-child{margin-top:0}
  textarea.field{min-height:84px;resize:vertical}
  .acts{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
  .btn{border:1px solid var(--bd);background:var(--pn);border-radius:6px;padding:7px 12px;text-decoration:none;color:var(--ink);display:inline-block;font-size:14px}
  .btn:hover{border-color:var(--ac)}
  .btn.pri{background:var(--ac);border-color:var(--ac);color:var(--pn);font-weight:600}
  .btn.wa{display:inline-flex;align-items:center;gap:6px}
  .btn.ok{background:var(--ac);border-color:var(--ac);color:var(--pn)}
  .hint{font-size:13px;color:var(--mut);margin-top:8px}
  .hist{margin:8px 0 0;padding-left:16px;font-size:13px;color:var(--mut)}
  .msgs{display:grid;gap:14px}
  .msg{border-left:3px solid var(--bd);padding:2px 0 2px 16px}
  .msg .mt{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:4px}
  .msg .mt b{font-family:var(--disp)}
  .msg .mt span{font-size:13px;color:var(--mut)}
  .msg p{margin:0 0 8px;white-space:pre-wrap;max-width:68ch}
  .note{font-size:12.5px;color:var(--mut);max-width:70ch;margin-top:10px}
  #toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--pn);padding:9px 16px;border-radius:6px;z-index:20;opacity:0;transition:opacity .2s;pointer-events:none}
  #toast.show{opacity:1}
  .none{display:grid;place-items:center;height:100%;color:var(--mut);padding:24px;text-align:center}

  [hidden]{display:none!important}
  .aviso{margin-top:12px;border-left:3px solid var(--warn);background:var(--warnbg);color:var(--ink);border-radius:0 6px 6px 0;padding:8px 12px;font-size:13px}
  .sb-head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
  .job{margin-top:12px;border:1px solid var(--bd);background:var(--pn);border-radius:6px;padding:10px 12px;font-size:13px}
  .job b{display:block;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .job .st{color:var(--mut);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:2px}
  .job .prog{height:4px;border-radius:2px;background:var(--bd2);overflow:hidden;margin:8px 0}
  .job .prog i{display:block;height:100%;background:var(--ac);transition:width .4s}
  .job .prog.ind i{width:35%!important;animation:vai 1.3s ease-in-out infinite alternate}
  @keyframes vai{from{margin-left:0}to{margin-left:65%}}
  .job.err{border-color:var(--bad)}.job.err b{color:var(--bad)}
  .job .acts{margin-top:8px}.job .btn{padding:3px 10px;font-size:13px}
  dialog{border:1px solid var(--bd);border-radius:10px;background:var(--pn);color:var(--ink);padding:24px;width:min(440px,calc(100vw - 32px))}
  dialog::backdrop{background:rgba(18,23,27,.55)}
  dialog h2{font:700 20px/1.2 var(--disp);margin:0 0 4px}
  dialog p{margin:0 0 14px;color:var(--mut);font-size:13.5px}
  dialog label{margin-top:12px}
  dialog .chk{display:flex;gap:8px;align-items:center;color:var(--ink);margin-top:14px}
  dialog .acts{margin-top:18px}
  .formerr{color:var(--bad);font-size:13px;margin-top:10px;min-height:1em}
  @media (max-width:1100px){.top{grid-template-columns:1fr}.dial{max-width:300px}}
  @media (max-width:900px){
    body{grid-template-columns:1fr;overflow:auto;padding-bottom:58px}
    #nav{position:fixed;bottom:0;left:0;right:0;height:58px;flex-direction:row;justify-content:center;gap:24px;padding:0;z-index:20}
    #kanban{grid-column:1;height:calc(100vh - 58px)}
    #sb{height:calc(100vh - 58px)}
    #main{display:none;height:100vh}
    body.det #sb{display:none}body.det #main{display:block}
    .back{display:inline-block}
    .sheet{padding:18px 16px 56px}
    .sec{grid-template-columns:1fr}
    dl{grid-template-columns:100px 1fr}
  }
  @media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<nav id="nav" aria-label="Seções">
  <button class="tg" id="nav-tg" title="Expandir ou recolher o menu" aria-label="Expandir ou recolher o menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></button>
  <button data-view="leads" aria-current="page" title="Leads"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.500-3.500"/></svg>Leads</button>
  <button data-view="crm" title="CRM"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="5" height="16" rx="1"/><rect x="10" y="4" width="5" height="10" rx="1"/><rect x="17" y="4" width="4" height="13" rx="1"/></svg>CRM</button>
  <button data-view="fila" title="Fila de envio"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10"/></svg>Fila</button>
  <button data-view="wpp" title="WhatsApp"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8.500 8.500 0 0 1-12.700 7.400L3 21l1.600-5.200A8.500 8.500 0 1 1 21 12z"/></svg>WhatsApp</button>
</nav>
<aside id="sb" aria-label="Clientes">
  <div class="sb-top">
    <div class="sb-head"><div><h1 id="titulo">Leads</h1>
    <p id="resumo"></p></div>
    <button class="btn pri" id="novo" hidden>Buscar leads</button></div>
    <div id="job" hidden aria-live="polite"></div>
    <div class="aviso" id="aviso" hidden>Versão sem servidor: não dá para buscar leads aqui. No terminal, rode <b>python server.py</b> e abra <b>localhost:8765</b>.</div>
    <div class="dist" id="dist" role="img" aria-label="Distribuição por chance"></div>
    <div class="legend" id="legend"></div>
  </div>
  <div class="find">
    <input class="field" id="q" type="search" placeholder="Buscar nome, bairro ou telefone" aria-label="Buscar">
    <div class="niches" id="niches" role="group" aria-label="Nicho"></div>
    <div class="two">
      <select class="field" id="f" aria-label="Chance">
        <option value="">Toda chance</option>
        <option value="alta">Alta (65%+)</option>
        <option value="media">Média (40–64%)</option>
        <option value="baixa">Baixa (&lt;40%)</option>
      </select>
      <select class="field" id="s" aria-label="Status">
        <option value="">Todo status</option>
        <option value="novo">Novo</option>
        <option value="enviado">Contato enviado</option>
        <option value="respondeu">Respondeu</option>
        <option value="reuniao">Reunião marcada</option>
        <option value="fechado">Fechado</option>
        <option value="sem">Sem interesse</option>
        <option value="renovar">Renovar contato</option>
      </select>
    </div>
    <select class="field" id="o" aria-label="Ordenar">
      <option value="chance">Maior chance primeiro</option>
      <option value="qtd">Mais avaliações</option>
      <option value="nome">Nome (A–Z)</option>
    </select>
  </div>
  <div class="count" id="count" aria-live="polite"></div>
  <div id="list" role="list"></div>
</aside>
<main id="main" tabindex="-1"></main>
<section id="kanban" aria-label="CRM">
  <div class="kb-top"><div><h1>CRM</h1><p>Arraste os cartões entre as colunas (a cor do cartão muda junto). Arraste o título de uma etapa para mudar a posição dela. Use o quadradinho de cor, o lápis e o + para personalizar as etapas. Clique num cartão para abrir o lead.</p></div><button class="btn" id="kb-reset">Restaurar cores</button></div>
  <div class="kb-board" id="kb-board"></div>
</section>
<section id="fila" aria-label="Fila de envio">
  <div class="kb-top"><div><h1>Fila de envio</h1><p>Primeiro contato automático pelo WhatsApp conectado. Só sai o que estiver aprovado, dentro do limite diário, do horário e do intervalo escolhidos.</p></div></div>
  <div class="wp-box" style="max-width:980px">
    <div class="wp-st off" id="fl-st"><i></i><span id="fl-tx">...</span></div>
    <p id="fl-sub"></p>
    <label class="chk" style="display:flex;gap:8px;align-items:center;margin:8px 0"><input type="checkbox" id="fl-ativo"> <b>Envio automático ligado</b></label>
    <div class="fl-cfg">
      <label>Limite por dia<input class="field" type="number" min="1" max="500" id="fl-limite"></label>
      <label>Intervalo mínimo (s)<input class="field" type="number" min="1" max="3600" id="fl-imin"></label>
      <label>Intervalo máximo (s)<input class="field" type="number" min="1" max="3600" id="fl-imax"></label>
      <label>Horário inicial<input class="field" type="time" id="fl-hini"></label>
      <label>Horário final<input class="field" type="time" id="fl-hfim"></label>
    </div>
    <label class="chk" style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="fl-auto"> Aprovar automaticamente o que entrar na fila</label>
    <h3 style="font:700 15px var(--disp);margin:16px 0 4px">Follow-ups automáticos</h3>
    <label class="chk" style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="fl-fu"> Criar follow-ups para quem recebeu a abertura e não respondeu</label>
    <div class="fl-cfg">
      <label>1º follow-up após (horas)<input class="field" type="number" min="1" max="720" id="fl-fu1"></label>
      <label>Fechamento após (dias)<input class="field" type="number" min="1" max="90" id="fl-fu2"></label>
      <label>Encerrar sem resposta após (dias)<input class="field" type="number" min="1" max="180" id="fl-enc"></label>
    </div>
    <label class="chk" style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="fl-encauto"> Mover para "Sem interesse" quem não responder depois de todo o ciclo</label>
    <p>Os follow-ups entram na fila como os demais (precisam de aprovação, a menos que "aprovar automaticamente" esteja ligado) e são cancelados se o cliente responder ou pedir para parar.</p>
    <div id="fl-opt"></div>
    <p>Dica: comece com poucos por dia e intervalos longos. Números novos enviando muita mensagem fria costumam ser bloqueados.</p>
    <div class="acts"><button class="btn pri" id="fl-bulk">Enfileirar aberturas</button><button class="btn" id="fl-aprovar">Aprovar todas pendentes</button><button class="btn" id="fl-limpar">Limpar concluídas</button></div>
    <div id="fl-err" role="alert" style="color:var(--bad);font-size:13px;min-height:1em;margin-top:8px"></div>
  </div>
  <div class="fl-wrap" id="fl-lista"></div>
</section>
<section id="wpp" aria-label="WhatsApp">
  <div class="kb-top"><div><h1>WhatsApp</h1><p>Conecte seu WhatsApp lendo o QR code. O painel usa o WhatsApp Web para enviar e receber as mensagens.</p></div></div>
  <div class="wp-box">
    <div class="wp-st off" id="wp-st"><i></i><span id="wp-tx">Verificando...</span></div>
    <p id="wp-sub"></p>
    <img id="wp-qr" alt="QR code para parear o WhatsApp" hidden>
    <p id="wp-help" hidden>No celular: WhatsApp &gt; Aparelhos conectados &gt; Conectar um aparelho, e aponte para o QR code.</p>
    <div class="acts"><button class="btn pri" id="wp-con">Conectar número</button><button class="btn" id="wp-sair" hidden>Fechar navegador</button></div>
    <div id="wp-err" role="alert"></div>
  </div>
  <div class="wp-box" id="vr-box">
    <div class="wp-st"><span>Verificar telefones dos leads</span></div>
    <p>Abre cada número no WhatsApp Web só para ver se existe uma conta. Nada é enviado. Leva uns 3 a 6 segundos por número, e o resultado fica salvo no banco.</p>
    <div class="job" id="vr-st" style="margin:10px 0"></div>
    <div class="acts"><button class="btn pri" id="vr-go">Verificar números pendentes</button><button class="btn" id="vr-x" hidden>Cancelar</button></div>
    <div id="vr-err" role="alert" style="color:var(--bad);font-size:13px;min-height:1em;margin-top:8px"></div>
  </div>
</section>
<div id="toast" role="status"></div>
<dialog id="dlg-lead" aria-labelledby="dl-t"></dialog>
<dialog id="dlg" aria-labelledby="dlg-t">
  <form id="fnovo" novalidate>
    <h2 id="dlg-t">Buscar novos leads</h2>
    <p>Coleta os negócios no Google Maps e detalha cada um. Quando terminar, eles entram na lista sozinhos.</p>
    <label for="n-nicho">Nicho</label>
    <input class="field" id="n-nicho" maxlength="80" placeholder="Ex.: Borracharias" autocomplete="off" required>
    <label for="n-cidade">Cidade</label>
    <input class="field" id="n-cidade" maxlength="80" placeholder="Ex.: Guarapuava, PR" autocomplete="off" required>
    <label for="n-lim">Limite de negócios (opcional)</label>
    <input class="field" id="n-lim" type="number" min="1" max="500" placeholder="Todos os encontrados">
    <label class="chk"><input type="checkbox" id="n-vis"> Mostrar o navegador durante a busca</label>
    <div class="formerr" id="n-err" role="alert"></div>
    <div class="acts"><button class="btn pri" type="submit">Iniciar busca</button><button class="btn" type="button" id="n-x">Cancelar</button></div>
  </form>
</dialog>

<script>

/* ====== CONFIGURE AQUI ====== */
const SEU_NOME = "Adriano";
const VAGAS = 3;
const PRODUTOS = {
  site:     {nome:"Site profissional",            curiosidade:"quem pesquisa o nome de vocês no Google não encontra um site, só o mapa",
             beneficio:"colocar {nome} no Google com um site que gera pedido de orçamento",
             perda:"cada dia sem site é cliente que pesquisa, não acha e liga pro concorrente",
             oferta:"site no ar em poucos dias com condição especial de lançamento"},
  whatsapp: {nome:"Atendimento automático no WhatsApp", curiosidade:"muita gente chama no WhatsApp e quem demora para responder perde o cliente",
             beneficio:"responder o cliente em segundos, 24h, e já registrar o pedido sem você parar o serviço",
             perda:"cliente que não é respondido na hora chama o próximo da lista",
             oferta:"robô de atendimento configurado e rodando, com condição especial de lançamento"},
  google:   {nome:"Perfil do Google otimizado",   curiosidade:"o perfil de vocês no Google tem espaço para aparecer bem mais acima nas buscas da região",
             beneficio:"subir {nome} nas buscas do mapa com fotos, posts e avaliações bem trabalhados",
             perda:"quem aparece primeiro no mapa leva a maior parte das ligações",
             oferta:"otimização completa do perfil com condição especial de lançamento"},
  social:   {nome:"Presença no Instagram/Facebook", curiosidade:"não achei um perfil ativo de vocês nas redes, e é onde o cliente confere antes de ligar",
             beneficio:"mostrar o trabalho de {nome} nas redes e gerar confiança antes do primeiro contato",
             perda:"cliente que não encontra o negócio nas redes desconfia e desiste",
             oferta:"perfil montado + 12 posts prontos com condição especial de lançamento"},
};
/* ============================ */

const SERVIDOR = __SERVIDOR__;
const LEADS = __LEADS__;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = v => parseFloat(String(v).replace(",", ".")) || 0;
const clamp = n => Math.max(5, Math.min(92, Math.round(n)));

function limparHorarios(h){
  if(!h) return [];
  h = h.replace(/[   ]/g," ").replace(/[​-‏⁠-]/g,"");
  h = h.split(" | 5 | 4")[0].replace(/\s*Os horários podem ser diferentes/g,"").replace(/\(Dia de Finados\)/g,"");
  return h.split(" | ").map(p=>{
    const m = p.match(/^(segunda-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sábado|domingo)\s*(.*)$/i);
    return m ? [m[1], (m[2].replace(/(\d{1,2}:\d{2})(?=\d{1,2}:\d{2})/g,"$1 e ").trim())||"—"] : null;
  }).filter(Boolean);
}
let WA = {};  // número (55DDD...) -> true/false, preenchido pelo servidor
let NICHOS = [];
const recalcNichos = ()=>{ NICHOS=[...new Map(LEADS.map(l=>[l.nicho_id,{id:l.nicho_id,nome:l.nicho_nome}])).values()]; };
recalcNichos();
const STATUS = {novo:"Novo",enviado:"Contato enviado",respondeu:"Respondeu",reuniao:"Reunião marcada",fechado:"Fechado",sem:"Sem interesse"};
let CRM = {}; try{ CRM = JSON.parse(localStorage.getItem("crm_leads")||"{}"); }catch{}
let tSync=null;
const salvarCRM = ()=>{
  try{ localStorage.setItem("crm_leads",JSON.stringify(CRM)); }catch{}
  if(!SERVIDOR) return;
  clearTimeout(tSync); tSync=setTimeout(enviarCRM,400);
};
async function enviarCRM(){
  tSync=null;
  try{
    const r=await api("/api/crm",{crm:CRM});
    for(const k in r.atu||{}) if(CRM[k]) CRM[k].atu=r.atu[k];
    if((r.conflitos||[]).length){ toast("O servidor atualizou "+r.conflitos.length+" lead(s) (resposta ou envio automático)"); sincronizarCRM(); }
  }catch{ toast("Não consegui salvar o CRM no servidor"); }
}
const crm = l => CRM[l.link] || (CRM[l.link]={status:"novo",notas:"",proximo:"",hist:[]});
const hoje = ()=>new Date().toISOString().slice(0,10);
const fmtD = iso => iso ? iso.slice(8,10)+"/"+iso.slice(5,7) : "";
const fmtDH = iso => fmtD(iso)+" "+iso.slice(11,16);
const addDias = n => { const d=new Date(); d.setDate(d.getDate()+n); return d.toISOString().slice(0,10); };
const renovar = l => { const c=CRM[l.link]; return !!c && ["enviado","respondeu"].includes(c.status) && c.proximo && c.proximo<=hoje(); };
function badge(l){
  const c=CRM[l.link]; if(!c||c.status==="novo") return "";
  const ult = c.status==="enviado" && c.hist.length ? " em "+fmtD(c.hist[c.hist.length-1].d) : "";
  return `<span class="badge cor st-${c.status}" style="--c:var(--c-${c.status})">${esc(STATUS[c.status]||c.status)}${ult}</span>`+(renovar(l)?`<span class="badge st-renovar">Renovar contato</span>`:"");
}
function toast(t){ const e=$("#toast"); e.textContent=t; e.classList.add("show"); clearTimeout(toast.t); toast.t=setTimeout(()=>e.classList.remove("show"),1800); }
const seguintes=(l,k)=>[1,2].map(i=>{ const x=mensagens(l,k)[i]; return {etapa:x.titulo.replace(/^\d\.\s*/,""),txt:x.txt,tag:x.tag}; });
function marcarEnviado(l,etapa,m){
  const c=crm(l);
  if(c.status==="novo") c.status="enviado";
  c.hist.push({d:new Date().toISOString(),etapa,...(m?{produto:PRODUTOS[prod].nome,tag:m.tag,txt:m.txt}:{}),
    ...(m&&etapa==="Abertura"&&l.wa?{numero:l.wa,nome:l.nome,seg:seguintes(l,prod)}:{})});
  if(c.hist.length>1) c.proximo=addDias(3); else if(!c.proximo) c.proximo=addDias(2);
  salvarCRM(); toast("Contato registrado: "+etapa);
}

const ICONE_WA=`<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M20.5 3.5A11.8 11.8 0 0 0 12 0 12 12 0 0 0 1.6 17.9L0 24l6.3-1.6A12 12 0 1 0 20.5 3.5zM12 21.8a9.8 9.8 0 0 1-5-1.4l-.4-.2-3.7 1 1-3.6-.2-.4A9.8 9.8 0 1 1 12 21.8zm5.4-7.3c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.1l-.9 1.1c-.2.2-.3.2-.6.1a8 8 0 0 1-4-3.500c-.3-.5.3-.5.8-1.500.1-.2 0-.4 0-.5l-.9-2.200c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.400s1 2.800 1.200 3c.1.200 2 3.100 4.900 4.300 1.800.8 2.500.8 3.400.7.5-.1 1.700-.7 1.900-1.400.2-.7.2-1.200.2-1.400-.1-.1-.3-.2-.6-.3z"/></svg>`;

function enriquecer(l){
  l.nicho = l.nicho_id;
  const tel = (l.telefone||"").replace(/\D/g,"");
  l.temWa = ("55"+tel) in WA ? WA["55"+tel] : undefined;  // true/false se já verificado, senão undefined
  l.celular = /^\d{2}9\d{8}$/.test(tel) && l.temWa!==false;
  l.semTel = !tel;
  l.wa = tel && l.temWa!==false ? "55"+tel : "";
  l.nota = num(l.avaliacao); l.qtd = parseInt(l.qtd_avaliacoes)||0;
  l.horarioLista = limparHorarios(l.horarios);
  l.h24 = l.horarioLista.some(h=>/24 horas/i.test(h[1]));
  const m = (l.endereco||"").match(/-\s*([^,-]+),\s*([^,]+?)\s*-\s*[A-Z]{2}/);
  l.bairro = m ? m[1].trim() : ""; l.cidade = m ? m[2].trim() : "sua região";
  l.redes = l.redes_sociais ? l.redes_sociais.split("; ").map(r=>{const i=r.indexOf(": ");return [r.slice(0,i),r.slice(i+2)]}) : [];
  l.siteFraco = l.tem_site==="sim" && /googlenegocioslocais|business\.site|linktr\.ee|wixsite|sites\.google/i.test(l.site);
  l.semSite = l.tem_site!=="sim";
  l.scores = pontuar(l);
  const best = Object.entries(l.scores).sort((a,b)=>b[1].v-a[1].v)[0];
  l.melhor = best[0]; l.chance = best[1].v;
  l.nivel = l.chance>=65?"alta":l.chance>=40?"media":"baixa";
  return l;
}
function pontuar(l){
  const S = {};
  const add = (k,base)=>S[k]={v:base,why:[]};
  const p = (k,pts,why)=>{S[k].v+=pts;S[k].why.push((pts>0?"+":"")+pts+" · "+why)};
  add("site",10);
  if(l.semSite && !l.redes.length) p("site",45,"sem site e sem rede social");
  else if(l.semSite) p("site",30,"só tem rede social, sem site próprio");
  else if(l.siteFraco) p("site",30,"site é uma página genérica/gratuita");
  else p("site",-5,"já possui site próprio");
  if(l.qtd>=20) p("site",12,"negócio ativo ("+l.qtd+" avaliações)");
  if(l.qtd>=50) p("site",8,"movimento alto");
  if(l.nota>=4.5) p("site",5,"boa reputação");
  add("whatsapp",15);
  if(l.temWa===true) p("whatsapp",15,"número confirmado no WhatsApp");
  if(l.celular) p("whatsapp",30,"telefone é celular (provável WhatsApp)");
  else if(l.semTel) p("whatsapp",-30,"sem telefone no Google");
  else if(l.temWa===false) p("whatsapp",-30,"número sem WhatsApp");
  else p("whatsapp",-5,"telefone fixo");
  if(l.h24) p("whatsapp",15,"atende 24h, demanda fora do horário");
  if(l.qtd>=30) p("whatsapp",15,"alto volume de clientes");
  else if(l.qtd>=10) p("whatsapp",5,"volume médio de clientes");
  if(l.nota>=4.5) p("whatsapp",5,"boa reputação");
  add("google",15);
  if(l.qtd<10) p("google",30,"poucas avaliações ("+l.qtd+"): pouca visibilidade");
  else if(l.qtd<30) p("google",15,"avaliações abaixo do ideal");
  if(l.nota && l.nota<4.5) p("google",20,"nota "+l.avaliacao+" pode melhorar");
  if(!l.horarioLista.length) p("google",10,"perfil sem horários");
  if(l.celular) p("google",8,"contato direto por celular");
  if(l.qtd>=100) p("google",-10,"perfil já forte");
  add("social",10);
  if(!l.redes.length) p("social",40,"nenhuma rede social encontrada");
  else p("social",0,"já tem "+l.redes.map(r=>r[0]).join(", "));
  if(l.qtd>=20) p("social",10,"negócio com movimento");
  if(l.celular) p("social",10,"contato direto por celular");
  if(l.semTel) p("social",-15,"sem telefone no Google");
  for(const k in S) S[k].v = clamp(S[k].v);
  return S;
}
function mensagens(l,k){
  const P = PRODUTOS[k], f = t=>t.replaceAll("{nome}",l.nome);
  const prova = l.qtd>=5 && l.nota ? ` Vi que vocês têm nota ${l.avaliacao} com ${l.qtd} avaliações, parabéns pelo trabalho.` : "";
  return [
    {tag:"Prova social + Curiosidade", titulo:"1. Abertura", txt:
`Oi, tudo bem? Aqui é o ${SEU_NOME}. Encontrei a ${l.nome} no Google.${prova}\n\nReparei que ${P.curiosidade}. Posso te mostrar em 2 minutos como ${f(P.beneficio)}?`},
    {tag:"Perda + Escassez", titulo:"2. Follow-up (sem resposta em 24h)", txt:
`${l.nome}, voltando rápido: ${P.perda}.\n\nEstou abrindo só ${VAGAS} vagas esta semana em ${l.cidade} com preço de lançamento. Quer que eu reserve uma pra você?`},
    {tag:"Reciprocidade + Oferta", titulo:"3. Fechamento", txt:
`Preparei um mini diagnóstico gratuito da ${l.nome} (já analisei seu perfil no Google). Sem compromisso.\n\nSe fizer sentido, fecho com você hoje: ${P.oferta}. Posso te mandar?`},
  ];
}
function ficha(l,k){
  const L = [`FICHA · ${l.nome}`,"",
    l.telefone && `Telefone: ${l.telefone}`,
    l.endereco && `Endereço: ${l.endereco}`,
    l.avaliacao && `Avaliação: ${l.avaliacao} (${l.qtd} avaliações)`,
    `Site: ${l.tem_site==="sim"?l.site:"não possui"}`,
    `Redes sociais: ${l.redes.length? l.redes.map(r=>r[0]+": "+r[1]).join(" | "):"nenhuma encontrada"}`,
    l.horarioLista.length && "Horários:\n"+l.horarioLista.map(h=>"  "+h[0]+": "+h[1]).join("\n"),
    "",`Oportunidade: ${PRODUTOS[k].nome} (${l.scores[k].v}% de chance)`,
    ...l.scores[k].why.map(w=>"  "+w)].filter(x=>x!==""&&x!==false&&x!==undefined);
  return L.join("\n");
}

let atual=null, prod=null, nichoSel="";
const COR = {alta:"#4CC3A4",media:"#F0B954",baixa:"#F2877D"};
const nivelDe = v => v>=65?"alta":v>=40?"media":"baixa";
const ARCO = Math.PI*90;
const mobile = () => innerWidth<=900;

function renderNiches(){
  const cont = id => LEADS.filter(l=>!id||l.nicho===id).length;
  const chip = (id,nome)=>`<button class="nc" data-n="${id}" aria-pressed="${nichoSel===id}">${esc(nome)}<span>${cont(id)}</span></button>`;
  $("#niches").innerHTML = chip("","Todos")+NICHOS.filter(n=>cont(n.id)).map(n=>chip(n.id,n.nome)).join("");
}
function renderResumo(){
  const B = LEADS.filter(l=>!nichoSel||l.nicho===nichoSel);
  const c = {alta:0,media:0,baixa:0}; B.forEach(l=>c[l.nivel]++);
  const t = B.length||1;
  const n = NICHOS.find(x=>x.id===nichoSel);
  $("#titulo").textContent = n ? n.nome : "Todos os nichos";
  $("#resumo").textContent = B.length+" negócios, "+B.filter(l=>l.semSite).length+" sem site próprio";
  $("#dist").innerHTML = ["alta","media","baixa"].map(k=>`<i class="${k}" style="width:${c[k]/t*100}%"></i>`).join("");
  $("#legend").innerHTML = `<span><b>${c.alta}</b> alta</span><span><b>${c.media}</b> média</span><span><b>${c.baixa}</b> baixa</span>`;
}
function filtrados(){
  const q = $("#q").value.toLowerCase(), f=$("#f").value, o=$("#o").value, st=$("#s").value;
  const stOk = l => !st || (st==="renovar"?renovar(l):((CRM[l.link]||{}).status||"novo")===st);
  const r = LEADS.filter(l=>(!f||l.nivel===f) && (!nichoSel||l.nicho===nichoSel) && stOk(l) && (!q || (l.nome+" "+l.bairro+" "+l.telefone).toLowerCase().includes(q)));
  r.sort(o==="nome"?(a,b)=>a.nome.localeCompare(b.nome):o==="qtd"?(a,b)=>b.qtd-a.qtd:(a,b)=>b.chance-a.chance);
  return r;
}
function render(manterFicha){
  const r = filtrados();
  if(!r.includes(atual)){ atual = mobile() ? null : (r[0]||null); if(atual) prod=atual.melhor; if(!manterFicha) painel(); }
  renderNiches(); renderResumo();
  $("#count").textContent = r.length+" de "+LEADS.length+" clientes";
  $("#list").innerHTML = r.length ? r.map(l=>`<button class="row" role="listitem" data-i="${LEADS.indexOf(l)}" ${l===atual?'aria-current="true"':""}>
    <span class="nm">${esc(l.nome)}</span><span class="pc ${l.nivel}">${l.chance}%</span>
    <span class="sub">${nichoSel?"":esc(l.nicho_nome)+" · "}${esc(l.bairro||l.cidade)} · ${esc(l.telefone||"sem telefone")}${statusTxt(l)}</span><span></span>
    <span class="meter"><i class="${l.nivel}" style="width:${l.chance}%"></i></span></button>`).join("")
    : LEADS.length ? `<div class="empty"><b>Nenhum cliente com esses filtros.</b>Limpe a busca ou escolha "Todos" nos nichos.</div>`
    : `<div class="empty"><b>Ainda não há leads.</b>${SERVIDOR ? "Use Buscar leads para coletar o primeiro nicho." : "Rode python server.py e use Buscar leads."}</div>`;
}
function statusTxt(l){ const c=CRM[l.link]; return c&&c.status!=="novo" ? " · "+STATUS[c.status]+(renovar(l)?", renovar":"") : ""; }

function dial(v,nivel){
  return `<svg viewBox="0 0 200 112" role="img" aria-label="Chance de conversão: ${v}%">
    <path class="trk" d="M10 100A90 90 0 0 1 190 100" fill="none" stroke-width="12" stroke-linecap="round"/>
    <path class="val" id="arc" d="M10 100A90 90 0 0 1 190 100" fill="none" stroke="${COR[nivel]}" stroke-width="12" stroke-linecap="round" stroke-dasharray="${ARCO}" stroke-dashoffset="${ARCO}"/>
  </svg>`;
}
function painel(){
  const m = $("#main"), l = atual;
  if(!l){ m.innerHTML = `<div class="none"><div><b>Escolha um cliente na lista.</b><br>A ficha, a chance de conversão e as mensagens aparecem aqui.</div></div>`; return; }
  const link = u=>`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(u.length>56?u.slice(0,53)+"…":u)}</a>`;
  const sc = l.scores[prod], nv = nivelDe(sc.v), msgs = mensagens(l,prod);
  m.innerHTML = `<div class="sheet">
  <button class="back" id="x">Voltar para a lista</button>
  <header class="head">
    <h2>${esc(l.nome)}</h2>
    <p class="addr">${esc(l.endereco||"Endereço não informado")}</p>
    <div id="badges">${badge(l)}</div>
  </header>
  <div class="top">
    <div class="dial">${dial(sc.v,nv)}<div class="big" style="color:${COR[nv]}">${sc.v}%</div>
      <div class="of">chance com ${esc(PRODUTOS[prod].nome.toLowerCase())}</div></div>
    <div>
      <div class="prods">${Object.keys(PRODUTOS).map(k=>{const v=l.scores[k].v;return `<button class="prod" data-p="${k}" aria-pressed="${k===prod}">
        <b>${esc(PRODUTOS[k].nome)}${k===l.melhor?'<span class="star">melhor opção</span>':""}</b><span class="p ${nivelDe(v)}">${v}%</span>
        <span class="meter"><i class="${nivelDe(v)}" style="width:${v}%"></i></span></button>`}).join("")}</div>
      <ul class="why">${sc.why.map(w=>`<li>${esc(w)}</li>`).join("")}</ul>
    </div>
  </div>

  <section class="sec"><h3>Dados do negócio</h3>
    <dl>
      <dt>Telefone</dt><dd>${esc(l.telefone||"—")} ${l.semTel?"":l.celular?"(celular)":"(fixo)"} · WhatsApp: ${l.temWa===true?"sim":l.temWa===false?"não":"não verificado"}</dd>
      <dt>Avaliação</dt><dd>${l.avaliacao?esc(l.avaliacao)+" de 5, com "+l.qtd+" avaliações":"—"}</dd>
      <dt>Site</dt><dd>${l.tem_site==="sim"?link(l.site)+(l.siteFraco?" <span class='hint'>(página genérica)</span>":""):"Não possui"}</dd>
      <dt>Redes sociais</dt><dd>${l.redes.length?l.redes.map(r=>esc(r[0])+": "+link(r[1])).join("<br>"):"Nenhuma encontrada"}</dd>
      <dt>Google Maps</dt><dd>${link(l.link)}</dd>
      <dt>Horários</dt><dd>${l.horarioLista.length?`<div class="hrs">${l.horarioLista.map(h=>`<span>${esc(h[0])}</span><span>${esc(h[1])}</span>`).join("")}</div>`:"—"}</dd>
    </dl>
  </section>

  <section class="sec"><h3>Acompanhamento<small>Fica salvo neste navegador.</small></h3>
    <div id="crm">${blocoCRM(l)}</div>
  </section>

  <section class="sec"><h3>Mensagens prontas<small>Copiar ou abrir no WhatsApp registra o contato.</small></h3>
    <div>
      <div class="msgs">${msgs.map((x,i)=>`<div class="msg"><div class="mt"><b>${esc(x.titulo.replace(/^\d\.\s*/,""))}</b><span>${esc(x.tag)}</span></div>
        <p>${esc(x.txt)}</p><div class="acts"><button class="btn" data-copy="${i}">Copiar mensagem</button>${SERVIDOR&&l.wa?`<button class="btn" data-fila="${i}" title="Entra na fila de envio automático">Adicionar à fila</button>`:""}${l.wa?`<a class="btn wa${l.celular?" pri":""}" data-wa="${i}" href="https://wa.me/${l.wa}?text=${encodeURIComponent(x.txt)}" target="_blank" rel="noopener" title="${l.celular?"Abrir conversa no WhatsApp":"Telefone fixo: pode não ter WhatsApp"}">${ICONE_WA} Enviar no WhatsApp${l.celular?"":" (fixo)"}</a>`:""}</div></div>`).join("")}</div>
      <div class="acts"><button class="btn" data-ficha>Copiar ficha completa</button></div>
      <p class="note">A porcentagem é uma estimativa por regras, a partir dos sinais do perfil no Google. Não é uma probabilidade medida. Ajuste pesos e produtos no início do script.</p>
    </div>
  </section></div>`;
  m.dataset.msgs = JSON.stringify(msgs.map(x=>x.txt));
  requestAnimationFrame(()=>requestAnimationFrame(()=>{ const a=$("#arc"); if(a) a.style.strokeDashoffset = ARCO*(1-sc.v/100); }));
}
function blocoCRM(l){
  const c=crm(l);
  return `<label for="c-st">Status</label>
    <select class="field" id="c-st">${Object.entries(STATUS).map(([k,v])=>`<option value="${k}" ${c.status===k?"selected":""}>${v}</option>`).join("")}</select>
    <label for="c-px">Renovar contato em</label>
    <input class="field" type="date" id="c-px" value="${esc(c.proximo)}">
    <div class="acts"><button class="btn" data-dias="2">Em 2 dias</button><button class="btn" data-dias="7">Em 7 dias</button><button class="btn" data-dias="0">Limpar data</button></div>
    <label for="c-nt">Anotações</label>
    <textarea class="field" id="c-nt" placeholder="Ex.: falou com o dono, pediu retorno na sexta.">${esc(c.notas)}</textarea>
    <div class="hint" id="c-ok"></div>
    ${c.hist.length?`<ul class="hist">${c.hist.slice(-6).reverse().map(h=>`<li>${fmtDH(h.d)}: ${esc(h.etapa)} enviado</li>`).join("")}</ul>`:`<div class="hint">Nenhum contato registrado.</div>`}`;
}
async function copiar(btn,txt){
  try{ await navigator.clipboard.writeText(txt); }
  catch{ const t=document.createElement("textarea"); t.value=txt; document.body.append(t); t.select(); document.execCommand("copy"); t.remove(); }
  const old=btn.textContent; btn.textContent="Copiado"; btn.classList.add("ok");
  setTimeout(()=>{btn.textContent=old;btn.classList.remove("ok")},1400);
}
function recarregarCRM(){ const c=$("#crm"); if(c) c.innerHTML=blocoCRM(atual); const b=$("#badges"); if(b) b.innerHTML=badge(atual); render(true); }
function abrir(i){ atual=LEADS[i]; prod=atual.melhor; painel(); render(true); document.body.classList.add("det"); $("#main").scrollTop=0; }
function voltar(){ document.body.classList.remove("det"); if(mobile()){ atual=null; painel(); render(true); } }

LEADS.forEach(enriquecer);
["q","f","o","s"].forEach(id=>$("#"+id).addEventListener("input",()=>render()));
$("#niches").addEventListener("click",e=>{ const b=e.target.closest("[data-n]"); if(b){ nichoSel=b.dataset.n; render(); } });
$("#list").addEventListener("click",e=>{ const b=e.target.closest(".row"); if(b) abrir(+b.dataset.i); });
$("#list").addEventListener("keydown",e=>{
  if(e.key!=="ArrowDown"&&e.key!=="ArrowUp") return;
  const rows=[...document.querySelectorAll(".row")], i=rows.indexOf(document.activeElement); if(i<0) return;
  e.preventDefault(); const n=rows[i+(e.key==="ArrowDown"?1:-1)]; if(n){ n.focus(); if(!mobile()) n.click(), n.focus(); }
});
$("#main").addEventListener("click",e=>{
  const t=e.target;
  if(t.id==="x") voltar();
  else if(t.closest("[data-p]")){ prod=t.closest("[data-p]").dataset.p; painel(); }
  else if(t.dataset.copy!==undefined){ const i=+t.dataset.copy; copiar(t,JSON.parse($("#main").dataset.msgs)[i]); marcarEnviado(atual,mensagens(atual,prod)[i].titulo.replace(/^\d\.\s*/,""),mensagens(atual,prod)[i]); recarregarCRM(); }
  else if(t.dataset.fila!==undefined){ const m=mensagens(atual,prod)[+t.dataset.fila]; api("/api/fila/adicionar",{itens:[itemFila(atual,m)]}).then(r=>toast(r.novos?"Adicionada à fila (aba Fila)":"Já está na fila ou foi enviada")).catch(e=>toast(e.message)); }
  else if(t.closest("a[data-wa]")){
    const i=+t.closest("a[data-wa]").dataset.wa, m=mensagens(atual,prod)[i], l=atual;
    const reg=()=>{ marcarEnviado(l,m.titulo.replace(/^\d\.\s*/,""),m); if(atual===l) recarregarCRM(); };
    if(SERVIDOR){ e.preventDefault(); enviarWpp(t.closest("a[data-wa]"),l,m.txt,reg); } else reg();
  }
  else if(t.dataset.dias!==undefined){ const n=+t.dataset.dias; crm(atual).proximo=n?addDias(n):""; salvarCRM(); recarregarCRM(); }
  else if(t.hasAttribute("data-ficha")) copiar(t,ficha(atual,prod));
});
$("#main").addEventListener("change",e=>{
  if(!atual) return;
  if(e.target.id==="c-st"){ const c=crm(atual); c.status=e.target.value; if(["enviado","respondeu"].includes(c.status)&&!c.proximo) c.proximo=addDias(2); if(c.status==="enviado"&&!c.hist.length) c.hist.push({d:new Date().toISOString(),etapa:"Contato manual"}); salvarCRM(); recarregarCRM(); }
  else if(e.target.id==="c-px"){ crm(atual).proximo=e.target.value; salvarCRM(); recarregarCRM(); }
});
$("#main").addEventListener("input",e=>{
  if(atual && e.target.id==="c-nt"){ crm(atual).notas=e.target.value; salvarCRM(); const o=$("#c-ok"); if(o) o.textContent="Anotação salva."; }
});
/* ---- navegação e Kanban do CRM ---- */
const PADRAO_COLS = [
  {id:"enviado",  nome:"1º contato enviado", desc:"Abertura enviada, aguardando resposta", cor:"#3b82f6"},
  {id:"respondeu",nome:"Respondeu",          desc:"Conversa em andamento",                 cor:"#f59e0b"},
  {id:"reuniao",  nome:"Reunião marcada",    desc:"Apresentação ou proposta combinada",    cor:"#8b5cf6"},
  {id:"fechado",  nome:"Fechado",            desc:"Virou cliente",                         cor:"#22c55e"},
  {id:"sem",      nome:"Sem interesse",      desc:"Não contatar de novo",                  cor:"#ef4444"}];
const FIXAS = new Set(PADRAO_COLS.map(c=>c.id));   // o sistema usa estas etapas; não podem ser excluídas
const PALETA = ["#14b8a6","#ec4899","#eab308","#06b6d4","#f97316","#84cc16","#a855f7","#64748b"];
function colsValidas(l){
  const ok = l.filter(c=>c&&typeof c.id==="string"&&/^(enviado|respondeu|reuniao|fechado|sem|c_[a-z0-9]{3,16})$/.test(c.id))
    .map(c=>({id:c.id,nome:String(c.nome||c.id).slice(0,40),desc:String(c.desc||"").slice(0,80),cor:/^#[0-9a-f]{6}$/i.test(c.cor)?c.cor:"#64748b"}));
  PADRAO_COLS.forEach(p=>{ if(!ok.some(c=>c.id===p.id)) ok.push({...p}); });
  return ok;
}
let COLS = PADRAO_COLS.map(c=>({...c}));
try{
  const l=JSON.parse(localStorage.getItem("crm_colunas")||"null");
  if(Array.isArray(l)&&l.length) COLS=colsValidas(l);
  else{ const lc=JSON.parse(localStorage.getItem("crm_cores")||"{}"); COLS.forEach(c=>{ if(lc[c.id]) c.cor=lc[c.id]; }); }  // cores salvas antes das etapas editáveis
}catch{}
/* mantém STATUS, as cores (--c-<etapa>) e o filtro de status iguais às etapas */
function sincCols(){
  for(const k of Object.keys(STATUS)) if(k!=="novo") delete STATUS[k];
  COLS.forEach(c=>{ STATUS[c.id]=c.nome; document.documentElement.style.setProperty("--c-"+c.id,c.cor); });
  const sel=$("#s"), v=sel.value;
  sel.innerHTML='<option value="">Todo status</option><option value="novo">Novo</option>'+COLS.map(c=>`<option value="${c.id}">${esc(c.nome)}</option>`).join("")+'<option value="renovar">Renovar contato</option>';
  sel.value=[...sel.options].some(o=>o.value===v)?v:"";
}
const salvarCols = ()=>{
  try{ localStorage.setItem("crm_colunas",JSON.stringify(COLS)); }catch{}
  if(SERVIDOR) api("/api/colunas",{colunas:COLS}).catch(()=>toast("Não consegui salvar as etapas no servidor"));
};
sincCols();
function mudarStatus(l,novo){
  const c=crm(l); c.status=novo;
  if(["enviado","respondeu"].includes(novo)&&!c.proximo) c.proximo=addDias(2);
  if(novo==="enviado"&&!c.hist.length) c.hist.push({d:new Date().toISOString(),etapa:"Contato manual"});
  salvarCRM();
}
function linhasCartao(l){
  const c=CRM[l.link]||{hist:[]}, u=c.hist[c.hist.length-1];
  let h = u ? `<span class="kb-line">Última ação: ${esc(u.etapa)} em ${fmtD(u.d)}</span>` : "";
  if(c.proximo && ["enviado","respondeu"].includes(c.status))
    h += renovar(l) ? `<span class="kb-line late">Follow-up atrasado desde ${fmtD(c.proximo)}</span>` : `<span class="kb-line">Próximo follow-up: ${fmtD(c.proximo)}</span>`;
  return h;
}
function renderKanban(){
  $("#kb-board").innerHTML = COLS.map(col=>{
    const st=col.id, vistos=new Set(), ls = LEADS.filter(l=>(CRM[l.link]||{}).status===st && !vistos.has(l.link) && vistos.add(l.link)).sort((a,b)=>(renovar(b)-renovar(a))||b.chance-a.chance);
    return `<div class="kb-col" data-st="${st}" style="--c:var(--c-${st})"><h2 draggable="true" data-col="${st}" title="Arraste para mudar a posição da etapa"><span class="kb-tt"><i></i>${esc(col.nome)}<label title="Trocar a cor desta etapa"><input type="color" data-cor="${st}" value="${col.cor}" aria-label="Cor da etapa ${esc(col.nome)}"></label><button class="kb-ic" data-ren="${st}" title="Renomear a etapa" aria-label="Renomear ${esc(col.nome)}">✎</button>${FIXAS.has(st)?"":`<button class="kb-ic" data-del="${st}" title="Excluir a etapa" aria-label="Excluir ${esc(col.nome)}">✕</button>`}</span><span class="cnt">${ls.length}</span></h2><div class="sub2">${esc(col.desc||"")}</div><div class="kb-cards">${
      ls.map(l=>`<button class="kb-card" style="--c:var(--c-${st})" draggable="true" data-i="${LEADS.indexOf(l)}"><b>${esc(l.nome)}</b><small>${esc(l.nicho_nome)} · ${esc(l.telefone||"sem telefone")}</small>${linhasCartao(l)}</button>`).join("")
      || '<div class="kb-empty">Nenhum cartão</div>'}</div></div>`;
  }).join("") + `<button class="kb-add" id="kb-add" title="Criar uma nova etapa">+ Adicionar etapa</button>`;
}
function novaEtapa(){
  const nome=(prompt("Nome da nova etapa:")||"").trim().slice(0,40); if(!nome) return;
  COLS.push({id:"c_"+Math.random().toString(36).slice(2,8),nome,desc:"",cor:PALETA[COLS.length%PALETA.length]});
  sincCols(); salvarCols(); renderKanban(); toast("Etapa criada: "+nome);
  const b=$("#kb-board"); b.scrollLeft=b.scrollWidth;
}
function excluirEtapa(id){
  const col=COLS.find(c=>c.id===id); if(!col||FIXAS.has(id)) return;
  const afetados=Object.entries(CRM).filter(([,c])=>c.status===id);
  if(!confirm(afetados.length?`Excluir "${col.nome}"? Os ${afetados.length} lead(s) dela voltam para "${STATUS.enviado}".`:`Excluir a etapa "${col.nome}"?`)) return;
  afetados.forEach(([,c])=>{ c.status="enviado"; });
  if(afetados.length) salvarCRM();
  COLS=COLS.filter(c=>c.id!==id); sincCols(); salvarCols(); renderKanban();
}
let cartao=null;
const tituloMsg = m => m.titulo.replace(/^\d\.\s*/,"");
const prodDe=(l,c)=>{ const u=[...c.hist].reverse().find(h=>h.produto); const k=u&&Object.keys(PRODUTOS).find(x=>PRODUTOS[x].nome===u.produto); return k||l.melhor; };
function proximaMsg(l,c){
  const i = c.status==="enviado" ? 1 : c.status==="respondeu" ? 2 : -1;
  return i<0 ? null : mensagens(l,prodDe(l,c))[i];
}
function abrirCartao(i){
  cartao=LEADS[i]; const l=cartao, c=crm(l), k=prodDe(l,c), sc=l.scores[k], m=proximaMsg(l,c);
  $("#dlg-lead").innerHTML=`
  <div class="hd"><div><h2 id="dl-t">${esc(l.nome)}</h2><small style="color:var(--mut)">${esc(l.nicho_nome)} · ${esc(l.bairro||l.cidade)}</small></div>
    <button class="btn" data-x>Fechar</button></div>
  <h3>Etapa no funil</h3>
  <select class="field" id="dl-st">${Object.entries(STATUS).map(([v,n])=>`<option value="${v}" ${c.status===v?"selected":""}>${n}</option>`).join("")}</select>
  <h3>Dados do cliente</h3>
  <dl><dt>Telefone</dt><dd>${esc(l.telefone||"—")} ${l.semTel?"":l.celular?"(celular)":"(fixo)"} · WhatsApp: ${l.temWa===true?"sim":l.temWa===false?"não":"não verificado"}</dd>
    <dt>Endereço</dt><dd>${esc(l.endereco||"—")}</dd>
    <dt>Avaliação</dt><dd>${l.avaliacao?esc(l.avaliacao)+" ("+l.qtd+" avaliações)":"—"}</dd>
    <dt>Site</dt><dd>${l.tem_site==="sim"?esc(l.site):"não possui"}</dd>
    <dt>Redes sociais</dt><dd>${l.redes.length?l.redes.map(r=>esc(r[0])).join(", "):"nenhuma encontrada"}</dd></dl>
  <h3>Por que abordamos: ${esc(PRODUTOS[k].nome)} (${sc.v}% de chance)</h3>
  <ul style="margin:0;padding-left:18px">${sc.why.map(w=>`<li>${esc(w)}</li>`).join("")}</ul>
  <h3>Passo a passo até agora</h3>
  ${c.hist.length?`<ol class="tl">${c.hist.map(h=>`<li><b>${esc(h.etapa)}</b> <span class="when">${fmtDH(h.d)}${h.produto?" · produto: "+esc(h.produto):""}${h.tag?" · técnica: "+esc(h.tag):""}</span>${h.txt?`<div class="quote">${esc(h.txt)}</div>`:`<div class="when">Texto não registrado</div>`}</li>`).join("")}</ol>`:"<p>Nenhum contato registrado ainda.</p>"}
  ${c.proximo&&["enviado","respondeu"].includes(c.status)?`<p><b>Próximo follow-up:</b> ${fmtD(c.proximo)}${renovar(l)?" (atrasado)":""}</p>`:""}
  ${m?`<h3>Próximo passo sugerido: ${esc(tituloMsg(m))}</h3><div class="quote">${esc(m.txt)}</div>
    <div class="acts"><button class="btn" data-dl-copy>Copiar mensagem</button>${l.wa?`<a class="btn wa pri" data-dl-wa href="https://wa.me/${l.wa}?text=${encodeURIComponent(m.txt)}" target="_blank" rel="noopener">${ICONE_WA} Enviar no WhatsApp</a>`:""}</div>`:""}
  <h3>Anotações</h3><textarea class="field" id="dl-nt" placeholder="Anote o que o cliente disse">${esc(c.notas)}</textarea>
  <div class="acts"><button class="btn" data-dl-ficha>Abrir ficha completa</button></div>`;
  if(!$("#dlg-lead").open) $("#dlg-lead").showModal();
}
function registrarProximo(){
  const c=crm(cartao), m=proximaMsg(cartao,c); prod=prodDe(cartao,c);
  marcarEnviado(cartao,tituloMsg(m),m); abrirCartao(LEADS.indexOf(cartao)); renderKanban();
}
$("#dlg-lead").addEventListener("click",e=>{
  const t=e.target; if(!cartao) return;
  if(t===$("#dlg-lead")||t.closest("[data-x]")) $("#dlg-lead").close();
  else if(t.closest("[data-dl-copy]")){ copiar(t,proximaMsg(cartao,crm(cartao)).txt); registrarProximo(); }
  else if(t.closest("[data-dl-wa]")){
    if(SERVIDOR){ e.preventDefault(); const m=proximaMsg(cartao,crm(cartao)); enviarWpp(t.closest("[data-dl-wa]"),cartao,m.txt,registrarProximo); }
    else setTimeout(registrarProximo,0);
  }
  else if(t.closest("[data-dl-ficha]")){ const i=LEADS.indexOf(cartao); $("#dlg-lead").close(); mostrar("leads"); abrir(i); }
});
$("#dlg-lead").addEventListener("change",e=>{ if(e.target.id==="dl-st"){ mudarStatus(cartao,e.target.value); abrirCartao(LEADS.indexOf(cartao)); renderKanban(); } });
$("#dlg-lead").addEventListener("input",e=>{ if(e.target.id==="dl-nt"){ crm(cartao).notas=e.target.value; salvarCRM(); } });
function mostrar(v){
  document.body.classList.toggle("crm",v==="crm");
  document.body.classList.toggle("wpp",v==="wpp");
  document.body.classList.toggle("fila",v==="fila");
  if(v==="fila") filaCarregar(); else clearTimeout(filaT);
  if(v==="wpp"){ wppStatus(); vrStatus(); } else { clearTimeout(wppT); clearTimeout(vrT); }
  document.querySelectorAll("#nav button").forEach(b=>b.dataset.view===v?b.setAttribute("aria-current","page"):b.removeAttribute("aria-current"));
  if(v==="crm") renderKanban(); else if(v==="leads") render(true);
}
/* ---- fila de envio automático ---- */
let filaT=null;
const itemFila=(l,m)=>({link:l.link,nome:l.nome,numero:l.wa,texto:m.txt,etapa:m.titulo.replace(/^\d\.\s*/,""),produto:PRODUTOS[prod||l.melhor].nome,tag:m.tag,seguintes:seguintes(l,prod||l.melhor)});
const FL_EST={pendente:"Aguardando aprovação",aprovada:"Aprovada",enviada:"Enviada",erro:"Erro",sem_whatsapp:"Sem WhatsApp"};
const elfoco=id=>document.activeElement&&document.activeElement.id===id;
async function filaCarregar(){
  clearTimeout(filaT);
  try{
    const r=await api("/api/fila"), c=r.config, e=r.estado;
    if(!elfoco("fl-limite")) $("#fl-limite").value=c.limite_dia;
    if(!elfoco("fl-imin")) $("#fl-imin").value=c.intervalo_min;
    if(!elfoco("fl-imax")) $("#fl-imax").value=c.intervalo_max;
    if(!elfoco("fl-hini")) $("#fl-hini").value=c.hora_ini;
    if(!elfoco("fl-hfim")) $("#fl-hfim").value=c.hora_fim;
    $("#fl-ativo").checked=c.ativo; $("#fl-auto").checked=c.auto_aprovar;
    $("#fl-fu").checked=c.followups_auto; $("#fl-encauto").checked=c.encerrar_auto;
    for(const [id,k] of [["fl-fu1","followup1_horas"],["fl-fu2","followup2_dias"],["fl-enc","encerrar_dias"]]) if(!elfoco(id)) $("#"+id).value=c[k];
    $("#fl-opt").innerHTML = (r.optouts||[]).length ? `<p><b>${r.optouts.length} número(s) pediram para parar</b> e nunca mais recebem mensagem: ${r.optouts.map(o=>`+${esc(o.numero)} <button class="btn" data-reativar="${esc(o.numero)}">Reativar</button>`).join(" · ")}</p>` : "";
    $("#fl-st").className="wp-st "+(c.ativo?"open":"off"); $("#fl-tx").textContent=c.ativo?"Ligado":"Desligado";
    $("#fl-sub").textContent=`${e.motivo}${e.proximo_em?" Próximo envio a partir de "+e.proximo_em+".":""} Enviados hoje: ${e.hoje} de ${c.limite_dia}.`;
    $("#fl-lista").innerHTML = r.itens.length ? r.itens.map(i=>`<div class="fl-row"><div><b>${esc(i.nome)}</b> · ${esc(i.etapa)} <small style="color:var(--mut)">(+${esc(i.numero)})</small></div>
      <div><span class="fl-st ${i.estado}">${FL_EST[i.estado]||i.estado}</span> ${i.estado==="pendente"?`<button class="btn" data-fa="aprovar" data-id="${i.id}">Aprovar</button>`:i.estado==="aprovada"?`<button class="btn" data-fa="pausar" data-id="${i.id}">Tirar da fila</button>`:""}${i.estado!=="enviada"?` <button class="btn" data-fa="remover" data-id="${i.id}">Remover</button>`:""}</div>
      <div class="tx">${esc(i.texto)}</div>${i.erro?`<div class="tx" style="color:var(--bad)">${esc(i.erro)}</div>`:""}</div>`).join("") : `<div class="empty"><b>A fila está vazia.</b>Use "Adicionar à fila" numa mensagem da ficha do lead, ou "Enfileirar aberturas".</div>`;
    const n=candidatos().length; $("#fl-bulk").textContent=`Enfileirar aberturas (${n} leads com WhatsApp confirmado)`; $("#fl-bulk").disabled=!n;
  }catch(e){ $("#fl-tx").textContent="Servidor indisponível"; }
  if(document.body.classList.contains("fila")) filaT=setTimeout(filaCarregar,4000);
}
const candidatos=()=>{ const v=new Set(); return LEADS.filter(l=>l.temWa===true&&l.wa&&((CRM[l.link]||{}).status||"novo")==="novo"&&!v.has(l.wa)&&v.add(l.wa)); };
async function filaCfg(){
  try{ await api("/api/fila/config",{config:{ativo:$("#fl-ativo").checked,auto_aprovar:$("#fl-auto").checked,limite_dia:$("#fl-limite").value,intervalo_min:$("#fl-imin").value,intervalo_max:$("#fl-imax").value,hora_ini:$("#fl-hini").value,hora_fim:$("#fl-hfim").value,followups_auto:$("#fl-fu").checked,encerrar_auto:$("#fl-encauto").checked,followup1_horas:$("#fl-fu1").value,followup2_dias:$("#fl-fu2").value,encerrar_dias:$("#fl-enc").value}}); $("#fl-err").textContent=""; filaCarregar(); }
  catch(e){ $("#fl-err").textContent=e.message; }
}
$("#fila").addEventListener("change",e=>{ if(e.target.matches(".wp-box input")) filaCfg(); });
$("#fl-bulk").addEventListener("click",async()=>{
  const cs=candidatos(); if(!cs.length) return;
  if(!confirm(`Colocar a mensagem de abertura de ${cs.length} lead(s) na fila?`+($("#fl-auto").checked?" Elas serão aprovadas automaticamente.":" Você ainda precisa aprovar.")+" Os envios respeitam o limite diário e o intervalo.")) return;
  const itens=cs.map(l=>{ const k=l.melhor, m=mensagens(l,k)[0]; return {link:l.link,nome:l.nome,numero:l.wa,texto:m.txt,etapa:m.titulo.replace(/^\d\.\s*/,""),produto:PRODUTOS[k].nome,tag:m.tag,seguintes:seguintes(l,k)}; });
  try{ const r=await api("/api/fila/adicionar",{itens}); toast(r.novos+" mensagem(ns) na fila"); filaCarregar(); }catch(e){ $("#fl-err").textContent=e.message; }
});
$("#fl-aprovar").addEventListener("click",async()=>{ await api("/api/fila/acao",{acao:"aprovar_todas"}); filaCarregar(); });
$("#fl-limpar").addEventListener("click",async()=>{ await api("/api/fila/acao",{acao:"limpar"}); filaCarregar(); });
$("#fl-opt").addEventListener("click",async e=>{ const b=e.target.closest("[data-reativar]"); if(b&&confirm("Reativar este número? Ele voltará a poder receber mensagens.")){ await api("/api/fila/reativar",{numero:b.dataset.reativar}); filaCarregar(); } });
$("#fl-lista").addEventListener("click",async e=>{ const b=e.target.closest("[data-fa]"); if(!b) return; await api("/api/fila/acao",{acao:b.dataset.fa,id:+b.dataset.id}); filaCarregar(); });
/* ---- conexão do WhatsApp (WhatsApp Web via Playwright) ---- */
async function enviarWpp(btn,l,txt,aoEnviar){
  if(btn.dataset.busy) return; btn.dataset.busy="1";
  const antes=btn.innerHTML; btn.textContent="Enviando...";
  try{
    const r=await api("/api/whatsapp/enviar",{numero:l.wa,texto:txt});
    if(r.ok){ toast("Mensagem enviada para "+l.nome); aoEnviar(); }
    else if(r.erro==="sem_whatsapp"){ toast("Esse número não tem WhatsApp"); }
    else{ toast(r.detalhe||"Não consegui enviar"); }
  }catch(err){ toast(err.message); }
  finally{ delete btn.dataset.busy; if(btn.isConnected) btn.innerHTML=antes; }
}
let wppT=null;
const WPP_TXT = {conectado:["Conectado","open"],qr:["Aguardando leitura do QR code","connecting"],iniciando:["Abrindo o WhatsApp Web...","connecting"],parado:["Desconectado","off"],erro:["Erro ao abrir o WhatsApp Web","off"]};
async function wppStatus(){
  clearTimeout(wppT);
  if(!SERVIDOR){ $("#wp-tx").textContent="Indisponível na página estática"; $("#wp-sub").textContent="Rode python server.py e abra localhost:8765."; $("#wp-con").hidden=true; return; }
  try{
    const r=await api("/api/whatsapp/status"), [t,c]=WPP_TXT[r.estado]||[r.estado,"off"];
    $("#wp-st").className="wp-st "+c; $("#wp-tx").textContent=t; $("#wp-err").textContent=r.erro||"";
    $("#wp-con").hidden = !["parado","erro"].includes(r.estado);
    $("#wp-sair").hidden = ["parado","erro"].includes(r.estado);
    $("#wp-qr").hidden = r.estado!=="qr"; if(r.estado==="qr") $("#wp-qr").src=r.qr;
    $("#wp-help").hidden = r.estado!=="qr";
    $("#wp-sub").textContent = r.estado==="conectado" ? "Pronto. A sessão fica salva: da próxima vez não precisa do QR code." : r.estado==="parado" ? "O navegador será aberto numa janela do Edge." : "";
  }catch(e){ $("#wp-st").className="wp-st off"; $("#wp-tx").textContent="Servidor indisponível"; $("#wp-err").textContent=e.message; }
  if(document.body.classList.contains("wpp")) wppT=setTimeout(wppStatus,2000);
}
/* ---- verificação de números no WhatsApp ---- */
let vrT=null, vrVisto="idle";
async function carregarWA(){
  try{ WA = await api("/api/whatsapp/numeros"); LEADS.forEach(enriquecer);
    if(document.body.classList.contains("crm")) renderKanban(); else { render(true); if(atual) painel(); } }catch{}
}
async function vrStatus(){
  clearTimeout(vrT);
  if(!SERVIDOR){ $("#vr-box").hidden=true; return; }
  try{
    const r=await api("/api/whatsapp/verificacao"), rodando=r.status==="running";
    $("#vr-go").hidden=rodando; $("#vr-x").hidden=!rodando;
    $("#vr-go").disabled = !rodando && r.pendentes===0;
    $("#vr-go").textContent = r.pendentes===0 && !rodando ? "Todos os números já foram verificados" : `Verificar números pendentes${r.pendentes?" ("+r.pendentes+")":""}`;
    $("#vr-st").hidden = r.status==="idle";
    $("#vr-st").innerHTML = rodando ? `Verificando ${r.atual} de ${r.total}... com WhatsApp: ${r.com} · sem: ${r.sem}<div class="prog"><i style="width:${r.total?100*r.atual/r.total:0}%"></i></div>`
      : r.status==="done" ? `Concluído: ${r.com} com WhatsApp, ${r.sem} sem.` : r.status==="cancelled" ? `Cancelado: ${r.com} com WhatsApp, ${r.sem} sem.` : r.status==="error" ? "" : "";
    $("#vr-err").textContent = r.status==="error" ? r.erro : "";
    if(rodando || r.status!==vrVisto){ if(rodando || vrVisto==="running") carregarWA(); }
    vrVisto=r.status;
    if(rodando && document.body.classList.contains("wpp")) vrT=setTimeout(vrStatus,2500);
  }catch{}
}
$("#vr-go").addEventListener("click",async()=>{ try{ await api("/api/whatsapp/verificar",{}); $("#vr-err").textContent=""; vrStatus(); }catch(e){ $("#vr-err").textContent=e.message; } });
$("#vr-x").addEventListener("click",async()=>{ await api("/api/whatsapp/verificar/cancel",{}); toast("Cancelando..."); });
if(SERVIDOR) carregarWA();
$("#wp-con").addEventListener("click",async()=>{ try{ await api("/api/whatsapp/conectar",{}); wppStatus(); }catch(e){ $("#wp-err").textContent=e.message; } });
$("#wp-sair").addEventListener("click",async()=>{ try{ await api("/api/whatsapp/sair",{}); toast("Navegador do WhatsApp fechado"); wppStatus(); }catch(e){ $("#wp-err").textContent=e.message; } });
const abrirNav = v => { document.body.classList.toggle("nav-open",v); try{ localStorage.setItem("nav_aberta",v?"1":"0"); }catch{} };
try{ if(localStorage.getItem("nav_aberta")==="1") document.body.classList.add("nav-open"); }catch{}
$("#nav").addEventListener("click",e=>{
  if(e.target.closest("#nav-tg")) return abrirNav(!document.body.classList.contains("nav-open"));
  const b=e.target.closest("[data-view]"); if(b){ abrirNav(true); mostrar(b.dataset.view); }
});
let arrastando=null, colArr=null;
const kb=$("#kb-board");
const limpaIns=()=>document.querySelectorAll(".kb-col.ins-antes,.kb-col.ins-depois,.kb-col.over").forEach(x=>x.classList.remove("ins-antes","ins-depois","over"));
kb.addEventListener("dragstart",e=>{
  const c=e.target.closest(".kb-card");
  if(c){ arrastando=+c.dataset.i; e.dataTransfer.effectAllowed="move"; e.dataTransfer.setData("text/plain",""); return; }
  const h=e.target.closest("h2[data-col]");
  if(h){ colArr=h.dataset.col; e.dataTransfer.effectAllowed="move"; e.dataTransfer.setData("text/plain",""); }
});
kb.addEventListener("dragover",e=>{
  const col=e.target.closest(".kb-col");
  if(colArr){ if(!col||col.dataset.st===colArr) return; e.preventDefault(); limpaIns(); const r=col.getBoundingClientRect(); col.classList.add(e.clientX<r.left+r.width/2?"ins-antes":"ins-depois"); return; }
  if(col&&arrastando!==null){ e.preventDefault(); document.querySelectorAll(".kb-col.over").forEach(x=>x!==col&&x.classList.remove("over")); col.classList.add("over"); }
});
kb.addEventListener("dragleave",e=>{ if(!e.relatedTarget||!e.relatedTarget.closest||!e.relatedTarget.closest(".kb-col")) limpaIns(); });
kb.addEventListener("drop",e=>{
  const col=e.target.closest(".kb-col");
  if(colArr){
    if(!col||col.dataset.st===colArr){ colArr=null; limpaIns(); return; }
    e.preventDefault(); const antes=col.classList.contains("ins-antes"); limpaIns();
    const [x]=COLS.splice(COLS.findIndex(c=>c.id===colArr),1); let i=COLS.findIndex(c=>c.id===col.dataset.st); if(!antes) i++;
    COLS.splice(i,0,x); colArr=null; sincCols(); salvarCols(); renderKanban(); return;
  }
  if(!col||arrastando===null) return;
  e.preventDefault(); const l=LEADS[arrastando]; arrastando=null; mudarStatus(l,col.dataset.st); renderKanban(); toast(l.nome+" → "+STATUS[col.dataset.st]);
});
kb.addEventListener("dragend",()=>{ arrastando=null; colArr=null; limpaIns(); });
kb.addEventListener("input",e=>{ const k=e.target.dataset.cor; if(k){ const c=COLS.find(x=>x.id===k); c.cor=e.target.value; document.documentElement.style.setProperty("--c-"+k,c.cor); } });
kb.addEventListener("change",e=>{ if(e.target.dataset.cor) salvarCols(); });
$("#kb-reset").addEventListener("click",()=>{ COLS.forEach(c=>{ const p=PADRAO_COLS.find(x=>x.id===c.id); if(p) c.cor=p.cor; }); sincCols(); salvarCols(); renderKanban(); toast("Cores restauradas"); });
kb.addEventListener("click",e=>{
  if(e.target.closest("label")) return;
  const ren=e.target.closest("[data-ren]");
  if(ren){ const c=COLS.find(x=>x.id===ren.dataset.ren), n=(prompt("Nome da etapa:",c.nome)||"").trim().slice(0,40); if(n){ c.nome=n; sincCols(); salvarCols(); renderKanban(); } return; }
  const del=e.target.closest("[data-del]"); if(del){ excluirEtapa(del.dataset.del); return; }
  if(e.target.closest("#kb-add")){ novaEtapa(); return; }
  const c=e.target.closest(".kb-card"); if(c) abrirCartao(+c.dataset.i);
});
document.addEventListener("keydown",e=>{ if(e.key==="Escape" && document.body.classList.contains("det")) voltar(); });
addEventListener("resize",()=>{ if(!mobile()) document.body.classList.remove("det"); });
render();

/* ---- busca de novos leads (só com python server.py) ---- */
async function api(path,body){
  const r = await fetch(path, body ? {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)} : undefined);
  const j = await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(j.erro||"Falha na requisição");
  return j;
}
async function recarregarLeads(foco){
  const novos = await api("/api/leads");
  LEADS.splice(0,LEADS.length,...novos.map(enriquecer));
  recalcNichos();
  if(foco && NICHOS.some(n=>n.id===foco)) nichoSel=foco;
  atual=null; render();
}
let versaoVista=-1, pollT=null;
function renderJob(j){
  const el=$("#job");
  if(j.status==="error"){ el.hidden=false; el.className="job err"; el.innerHTML=`<b>A busca falhou</b><div class="st" title="${esc(j.erro)}">${esc(j.erro)}</div><div class="acts"><button class="btn" data-job="fechar">Fechar</button></div>`; return; }
  if(j.status!=="running"){ el.hidden=true; return; }
  const det = j.etapa==="detalhando" && j.total;
  el.hidden=false; el.className="job";
  el.innerHTML=`<b>${det?"Detalhando":"Coletando"} ${esc(j.nicho)} em ${esc(j.cidade)}</b>
    <div class="prog ${det?"":"ind"}"><i style="width:${det?j.atual/j.total*100:0}%"></i></div>
    <div class="st">${det?j.atual+" de "+j.total+": "+esc(j.nome):"Lendo a lista do Google Maps..."}</div>
    <div class="acts"><button class="btn" data-job="cancelar">Cancelar busca</button></div>`;
}
async function poll(){
  clearTimeout(pollT);
  try{
    const j = await api("/api/job"); renderJob(j);
    if(versaoVista<0) versaoVista=j.versao;
    if(j.status==="done" && j.versao!==versaoVista){
      versaoVista=j.versao; const antes=LEADS.length; await recarregarLeads(j.nicho_id);
      toast(j.nicho+": "+Math.max(0,LEADS.length-antes)+" leads novos na lista");
    }
    if(j.status==="running") pollT=setTimeout(poll,1500);
  }catch{ pollT=setTimeout(poll,4000); }
}
if(!SERVIDOR) $("#aviso").hidden=false;
/* CRM no servidor (SQLite). Se o banco está vazio, sobe o que já existia no navegador. */
async function carregarCRMServidor(){
  try{
    const r = await api("/api/crm");
    if(Object.keys(r.crm||{}).length){ CRM=r.crm; try{ localStorage.setItem("crm_leads",JSON.stringify(CRM)); }catch{} }
    else if(Object.keys(CRM).length){ await enviarCRM(); toast("CRM do navegador copiado para o servidor"); }
    if((r.colunas||[]).length){ COLS=colsValidas(r.colunas); sincCols(); try{ localStorage.setItem("crm_colunas",JSON.stringify(COLS)); }catch{} }
    else if(Object.keys(r.cores||{}).length){ COLS.forEach(c=>{ if(r.cores[c.id]) c.cor=r.cores[c.id]; }); sincCols(); salvarCols(); }
    else if(JSON.stringify(COLS)!==JSON.stringify(PADRAO_COLS)) salvarCols();
    if(document.body.classList.contains("crm")) renderKanban(); else render(true);
  }catch{ toast("CRM do servidor indisponível; usando o do navegador"); }
}
if(SERVIDOR) carregarCRMServidor();
/* Traz do servidor o que mudou sozinho (respostas detectadas, envios automáticos) */
async function sincronizarCRM(){
  if(tSync) return;  // há alteração local esperando para ser salva
  try{
    const r=await api("/api/crm"); let mudou=false;
    for(const [k,srv] of Object.entries(r.crm||{})){
      const loc=CRM[k];
      if(loc && loc.atu===srv.atu) continue;
      const nome=(LEADS.find(l=>l.link===k)||{}).nome||"lead", u=srv.hist[srv.hist.length-1];
      if(u && u.auto && srv.hist.length>(loc?loc.hist.length:0)) toast(u.etapa==="Resposta do cliente" ? "Resposta de "+nome+": "+(u.txt||"").slice(0,60) : "Enviado para "+nome+": "+u.etapa);
      CRM[k]=srv; mudou=true;
    }
    if(!mudou) return;
    try{ localStorage.setItem("crm_leads",JSON.stringify(CRM)); }catch{}
    if(document.body.classList.contains("crm")){ renderKanban(); if(cartao&&$("#dlg-lead").open&&!$("#dlg-lead").contains(document.activeElement)) abrirCartao(LEADS.indexOf(cartao)); }
    else{ render(true); if(atual&&!$("#main").contains(document.activeElement)) recarregarCRM(); }
  }catch{}
}
if(SERVIDOR) setInterval(sincronizarCRM,8000);
if(SERVIDOR){
  $("#novo").hidden=false;
  $("#novo").addEventListener("click",()=>{ $("#n-err").textContent=""; $("#dlg").showModal(); $("#n-nicho").focus(); });
  $("#n-x").addEventListener("click",()=>$("#dlg").close());
  $("#fnovo").addEventListener("submit",async e=>{
    e.preventDefault();
    const nicho=$("#n-nicho").value.trim(), cidade=$("#n-cidade").value.trim();
    if(!nicho||!cidade){ $("#n-err").textContent="Preencha o nicho e a cidade."; return; }
    try{
      await api("/api/job",{nicho,cidade,limite:$("#n-lim").value,mostrar:$("#n-vis").checked});
      $("#dlg").close(); toast("Busca iniciada"); poll();
    }catch(err){ $("#n-err").textContent=err.message; }
  });
  $("#job").addEventListener("click",async e=>{
    const a=e.target.dataset.job; if(!a) return;
    if(a==="cancelar"){ await api("/api/job/cancel",{}); toast("Cancelando..."); }
    else $("#job").hidden=true;
  });
  poll();
}
</script>
</body>
</html>
'''


def carregar_leads():
    leads = []
    for arq in sorted(DADOS.glob("leads_detalhados_*.csv")):
        k = arq.stem.removeprefix("leads_detalhados_")
        meta = ler_meta(k)
        nicho_id = k.split("__")[0]
        with open(arq, encoding="utf-8-sig", newline="") as f:
            for lead in csv.DictReader(f):
                lead["nicho_id"] = nicho_id
                lead["nicho_nome"] = meta.get("nicho") or nicho_id.replace("-", " ").capitalize()
                lead["busca"] = meta.get("cidade", "")
                leads.append(lead)
    return leads


def renderizar(servidor=False):
    # "</" evita fechar a tag <script> por engano
    dados = json.dumps(carregar_leads(), ensure_ascii=False).replace("</", "<\\/")
    return HTML.replace("__LEADS__", dados).replace("__SERVIDOR__", "true" if servidor else "false")


def main():
    html = renderizar()
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(html, encoding="utf-8")
    print(f"{SAIDA.name} gerada (versão estática). Para buscar novos leads pela página, rode: python server.py")


if __name__ == "__main__":
    main()
