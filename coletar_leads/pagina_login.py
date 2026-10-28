"""Página de login, cadastro e primeiro acesso (criação do administrador). Servida em /login pelo server.py."""

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Entrar · Painel de leads</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#EDEFEC;--pn:#FFFFFF;--ink:#1C242B;--mut:#5B6770;--bd:#D9DDD8;
    --ac:#0E6F5C;--acbg:#DDEFEA;--bad:#A93226;--badbg:#F6DDD9;--ok:#0E6F5C;--okbg:#DDEFEA;
    --disp:"Bricolage Grotesque","Segoe UI",system-ui,sans-serif;
    --txt:"Public Sans","Segoe UI",system-ui,sans-serif;
  }
  @media (prefers-color-scheme:dark){:root{
    --bg:#12171B;--pn:#1A2127;--ink:#E6EAE7;--mut:#9AA6AF;--bd:#2B343B;
    --ac:#4CC3A4;--acbg:#173129;--bad:#F2877D;--badbg:#3A1E1B;--ok:#4CC3A4;--okbg:#173129}}
  *{box-sizing:border-box}
  html,body{min-height:100%}
  body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--txt);display:grid;place-items:center;padding:24px 16px}
  button,input{font:inherit;color:inherit}
  :focus-visible{outline:2px solid var(--ac);outline-offset:2px}
  main{width:100%;max-width:400px}
  main.largo{max-width:560px}
  .planos{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:4px 0 14px}
  .plano{position:relative;border:1px solid var(--bd);border-radius:10px;padding:10px;cursor:pointer;font-weight:400;margin:0}
  .plano input{position:absolute;opacity:0;width:1px;height:1px}
  .plano b{display:block;font:700 15px var(--disp)}
  .plano .preco{font-weight:600;font-size:13px}
  .plano small{display:block;color:var(--mut);font-size:11.5px;line-height:1.35;margin-top:4px}
  .plano:has(input:checked){border-color:var(--ac);box-shadow:0 0 0 3px var(--acbg)}
  .plano:has(input:focus-visible){outline:2px solid var(--ac);outline-offset:2px}
  .grupo{font-size:13px;font-weight:600;margin:0 0 6px}
  @media (max-width:480px){.planos{grid-template-columns:1fr}}
  .marca{display:flex;align-items:center;gap:10px;margin-bottom:18px}
  .marca i{width:36px;height:36px;border-radius:10px;background:var(--ac);display:grid;place-items:center;color:var(--pn)}
  .marca svg{width:20px;height:20px}
  .marca b{font:700 20px var(--disp)}
  .card{background:var(--pn);border:1px solid var(--bd);border-radius:14px;padding:24px}
  h1{font:700 22px/1.2 var(--disp);margin:0 0 6px}
  .sub{margin:0 0 18px;color:var(--mut);font-size:14px}
  .abas{display:grid;grid-template-columns:1fr 1fr;gap:4px;background:var(--bg);border-radius:10px;padding:4px;margin-bottom:18px}
  .abas button{border:0;background:none;border-radius:7px;padding:8px;font-weight:600;color:var(--mut);cursor:pointer}
  .abas button[aria-selected="true"]{background:var(--pn);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.08)}
  label{display:block;font-size:13px;font-weight:600;margin:0 0 12px}
  label span{display:block;margin-bottom:4px}
  input{width:100%;padding:10px 12px;border:1px solid var(--bd);border-radius:8px;background:var(--pn)}
  input:focus{border-color:var(--ac);outline:none;box-shadow:0 0 0 3px var(--acbg)}
  .senha{position:relative}
  .senha input{padding-right:64px}
  .senha button{position:absolute;right:6px;top:50%;transform:translateY(-50%);border:0;background:none;color:var(--ac);font-size:12px;font-weight:600;cursor:pointer;padding:6px}
  .dica{font-weight:400;color:var(--mut);font-size:12px;margin-top:4px}
  .pri{width:100%;border:0;border-radius:8px;padding:11px;background:var(--ac);color:var(--pn);font-weight:600;cursor:pointer;margin-top:6px}
  .pri:disabled{opacity:.6;cursor:wait}
  .msg{border-radius:8px;padding:10px 12px;font-size:14px;margin:0 0 14px}
  .msg.erro{background:var(--badbg);color:var(--bad)}
  .msg.ok{background:var(--okbg);color:var(--ok)}
  .rodape{text-align:center;color:var(--mut);font-size:12px;margin-top:16px}
  [hidden]{display:none!important}
</style>
</head>
<body>
<main>
  <div class="marca"><i><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.500-3.500"/></svg></i><b>Painel de leads</b></div>
  <div class="card">
    <div id="setup" hidden>
      <h1>Primeiro acesso</h1>
      <p class="sub">Crie a conta do <b>administrador da plataforma</b> (você). Ele aprova as empresas que se cadastrarem, define os planos e gerencia as contas.</p>
    </div>
    <div id="setup-remoto" hidden>
      <h1>Administrador ainda não criado</h1>
      <p class="sub">Por segurança, o primeiro administrador só pode ser criado no próprio computador do servidor. Abra <b>http://localhost:8765/login</b> nele.</p>
    </div>
    <div class="abas" id="abas" role="tablist" hidden>
      <button role="tab" id="t-entrar" aria-selected="true" aria-controls="form">Entrar</button>
      <button role="tab" id="t-criar" aria-selected="false" aria-controls="form">Criar conta</button>
    </div>
    <p class="msg" id="msg" role="alert" hidden></p>
    <form id="form" novalidate hidden>
      <label id="l-empresa" hidden><span>Nome da empresa</span><input id="empresa" autocomplete="organization" maxlength="80"></label>
      <div id="l-planos" hidden><p class="grupo">Plano</p><div class="planos" id="planos" role="radiogroup" aria-label="Plano"></div></div>
      <label id="l-nome" hidden><span>Seu nome</span><input id="nome" autocomplete="name" maxlength="80"></label>
      <label><span>E-mail</span><input id="email" type="email" autocomplete="username" maxlength="120" required></label>
      <label><span>Senha</span><div class="senha"><input id="senha" type="password" autocomplete="current-password" maxlength="200" required>
        <button type="button" id="ver" aria-label="Mostrar senha">Mostrar</button></div>
        <div class="dica" id="dica-senha" hidden>Pelo menos 8 caracteres.</div></label>
      <label id="l-senha2" hidden><span>Repita a senha</span><input id="senha2" type="password" autocomplete="new-password" maxlength="200"></label>
      <button class="pri" id="enviar" type="submit">Entrar</button>
    </form>
  </div>
  <p class="rodape" id="rodape">As senhas são guardadas criptografadas: nem o administrador consegue vê-las.</p>
</main>
<script>
const $=s=>document.querySelector(s);
let modo="entrar";
function msg(t,tipo){ const m=$("#msg"); m.hidden=!t; m.textContent=t||""; m.className="msg "+(tipo||"erro"); }
function definir(m){
  modo=m; msg("");
  const novo=m!=="entrar";
  $("#l-empresa").hidden=!novo; $("#l-planos").hidden=m!=="criar"; document.querySelector("main").classList.toggle("largo",m==="criar");
  $("#t-entrar").setAttribute("aria-selected",m==="entrar"); $("#t-criar").setAttribute("aria-selected",m==="criar");
  $("#l-nome").hidden=!novo; $("#l-senha2").hidden=!novo; $("#dica-senha").hidden=!novo;
  $("#senha").autocomplete=novo?"new-password":"current-password";
  $("#enviar").textContent=m==="entrar"?"Entrar":m==="setup"?"Criar administrador":"Criar conta";
  (novo?$("#empresa"):$("#email")).focus();
}
$("#t-entrar").onclick=()=>definir("entrar");
$("#t-criar").onclick=()=>definir("criar");
$("#ver").onclick=()=>{ const s=$("#senha"), v=s.type==="password"; s.type=v?"text":"password"; $("#senha2").type=s.type;
  $("#ver").textContent=v?"Ocultar":"Mostrar"; $("#ver").setAttribute("aria-label",v?"Ocultar senha":"Mostrar senha"); };
$("#form").addEventListener("submit",async e=>{
  e.preventDefault(); msg("");
  const corpo={email:$("#email").value.trim(),senha:$("#senha").value};
  if(modo!=="entrar"){
    corpo.nome=$("#nome").value.trim(); corpo.empresa=$("#empresa").value.trim();
    if(corpo.empresa.length<2) return msg("Informe o nome da empresa.");
    if(corpo.nome.length<2) return msg("Informe o seu nome.");
    if(modo==="criar"){ corpo.plano=(document.querySelector("input[name=plano]:checked")||{}).value; if(!corpo.plano) return msg("Escolha um plano."); }
    if(corpo.senha.length<8) return msg("A senha precisa ter pelo menos 8 caracteres.");
    if(corpo.senha!==$("#senha2").value) return msg("As duas senhas não são iguais.");
  }
  if(!corpo.email||!corpo.senha) return msg("Preencha e-mail e senha.");
  const b=$("#enviar"), txt=b.textContent; b.disabled=true; b.textContent="Aguarde...";
  try{
    const rota={entrar:"/api/auth/login",criar:"/api/auth/cadastro",setup:"/api/auth/setup"}[modo];
    const r=await fetch(rota,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(corpo)});
    const j=await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(j.erro||"Não foi possível continuar.");
    if(modo==="criar"){ $("#form").reset(); definir("entrar"); msg(j.mensagem||"Conta criada. Aguarde a aprovação.","ok"); }
    else location.replace("/");
  }catch(x){ msg(x.message); }
  b.disabled=false; b.textContent=txt;
});
fetch("/api/planos").then(r=>r.json()).then(j=>{
  const ps=Object.values(j.planos);
  $("#planos").innerHTML=ps.map((p,i)=>`<label class="plano"><input type="radio" name="plano" value="${p.id}"${i===1?" checked":""}>
    <b>${p.nome}</b><span class="preco">R$ ${p.preco}/mês</span>
    <small>${p.usuarios} usuário${p.usuarios>1?"s":""} · ${p.numeros} WhatsApp · ${p.leads_mes.toLocaleString("pt-BR")} leads/mês</small></label>`).join("");
}).catch(()=>{});
(async()=>{
  const r=await fetch("/api/auth/estado").then(r=>r.json()).catch(()=>({tem_usuarios:true}));
  if(r.logado) return location.replace("/");
  if(!r.tem_usuarios){
    if(!r.local){ $("#setup-remoto").hidden=false; return; }
    $("#setup").hidden=false; $("#form").hidden=false; definir("setup");
  }else{ $("#abas").hidden=false; $("#form").hidden=false; definir("entrar"); }
})();
</script>
</body>
</html>
"""
