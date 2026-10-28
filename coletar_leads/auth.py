"""Usuários, senhas e sessões do painel (banco da plataforma, ver contas.py).

Senhas nunca são guardadas legíveis: ficam como hash PBKDF2-SHA256 com sal próprio (ninguém, nem o admin,
consegue lê-las; quem gerencia troca a senha quando a pessoa esquece). A sessão é um código aleatório num
cookie HttpOnly; no banco fica só o hash desse código.

Papéis: `papel` é da plataforma ('admin' = você, que vê todas as contas; 'usuario' = cliente).
`papel_conta` é dentro da empresa ('dono' gerencia a equipe; 'membro' só usa o painel).
"""
import base64
import hashlib
import hmac
import re
import secrets
import threading
import time
from contextlib import closing
from datetime import datetime, timedelta

import contas
import planos

ITERACOES = 600_000
SESSAO_DIAS = 7
COOKIE = "painel_sessao"
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
SENHA_MIN = 8
# limite de tentativas de login: MAX_FALHAS erros em JANELA segundos bloqueiam o IP por JANELA segundos
MAX_FALHAS, JANELA = 5, 600
_FALHAS, _LOCK = {}, threading.Lock()


class ErroAuth(Exception):
    def __init__(self, msg, codigo=400):
        super().__init__(msg)
        self.codigo = codigo


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def hash_senha(senha):
    sal = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERACOES)
    return f"pbkdf2_sha256${ITERACOES}${base64.b64encode(sal).decode()}${base64.b64encode(h).decode()}"


def conferir_senha(senha, guardado):
    try:
        _, it, sal, h = guardado.split("$")
        novo = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), base64.b64decode(sal), int(it))
        return hmac.compare_digest(novo, base64.b64decode(h))
    except (ValueError, TypeError):
        return False


_HASH_FALSO = hash_senha(secrets.token_hex(8))  # usado quando o e-mail não existe, para o tempo de resposta ser igual

CAMPOS = ("u.id, u.nome, u.email, u.papel, u.status, u.criado, u.ultimo_login, u.trocar_senha, "
          "u.conta_id, u.papel_conta, k.nome, k.plano, k.status")
SELECT = f"SELECT {CAMPOS} FROM usuarios u LEFT JOIN contas k ON k.id=u.conta_id"


def _publico(row):
    p = planos.PLANOS.get(row[11] or "", {})
    return {"id": row[0], "nome": row[1], "email": row[2], "papel": row[3], "status": row[4],
            "criado": row[5], "ultimo_login": row[6], "trocar_senha": bool(row[7]), "papel_conta": row[9],
            "conta": {"id": row[8], "nome": row[10] or "", "plano": row[11] or "", "plano_nome": p.get("nome", ""),
                      "status": row[12] or ""}}


def _um(c, usuario_id):
    row = c.execute(SELECT + " WHERE u.id=?", (usuario_id,)).fetchone()
    return _publico(row) if row else None


def tem_usuarios():
    with closing(contas.con()) as c:
        return c.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone() is not None


def _validar(nome, email, senha):
    nome, email = (nome or "").strip(), (email or "").strip().lower()
    if not 2 <= len(nome) <= 80:
        raise ErroAuth("Informe o seu nome (de 2 a 80 letras).")
    if len(email) > 120 or not EMAIL.match(email):
        raise ErroAuth("E-mail inválido.")
    if not isinstance(senha, str) or not SENHA_MIN <= len(senha) <= 200:
        raise ErroAuth(f"A senha precisa ter pelo menos {SENHA_MIN} caracteres.")
    return nome, email


def _email_livre(c, email):
    if c.execute("SELECT 1 FROM usuarios WHERE email=?", (email,)).fetchone():
        raise ErroAuth("Já existe uma conta com este e-mail.", 409)


def _inserir(c, nome, email, senha, conta_id, papel_conta, papel="usuario", status="ativo", trocar=False):
    cur = c.execute("""INSERT INTO usuarios(nome,email,senha_hash,papel,status,criado,ultimo_login,trocar_senha,conta_id,papel_conta)
                       VALUES(?,?,?,?,?,?,'',?,?,?)""",
                    (nome, email, hash_senha(senha), papel, status, _agora(), int(trocar), conta_id, papel_conta))
    return cur.lastrowid


def _conta_nova(c, empresa, plano, status):
    try:
        conta = contas.criar(empresa, plano, status)
    except contas.ErroConta as e:
        raise ErroAuth(str(e), e.codigo)
    return conta["id"]


def criar_admin_inicial(empresa, nome, email, senha):
    """Primeiro acesso: cria o administrador da plataforma e a conta dele (plano Escala, ativa).
    Se a migração já criou a conta 1 sem dono (dados de antes das contas), ele vira o dono dela."""
    if tem_usuarios():
        raise ErroAuth("O administrador já foi criado. Entre com e-mail e senha.", 409)
    nome, email = _validar(nome, email, senha)
    sem_dono = contas.obter(1)
    if sem_dono and sem_dono["dono_id"] is None:
        conta_id = 1
    else:
        conta_id = _conta_nova(None, empresa, "escala", "ativa")
    with closing(contas.con()) as c:
        uid = _inserir(c, nome, email, senha, conta_id, "dono", papel="admin")
        c.execute("UPDATE contas SET dono_id=?, status='ativa'" + (", nome=?" if (empresa or "").strip() else "") + " WHERE id=?",
                  (uid, empresa.strip(), conta_id) if (empresa or "").strip() else (uid, conta_id))
        c.commit()
        return _um(c, uid)


def cadastrar(empresa, nome, email, senha, plano):
    """Cadastro público: cria a conta da empresa (aguardando aprovação) e o dono dela."""
    nome, email = _validar(nome, email, senha)
    if not planos.valido(plano):
        raise ErroAuth("Escolha um plano.")
    with closing(contas.con()) as c:
        _email_livre(c, email)
    conta_id = _conta_nova(None, empresa, plano, "pendente")
    with closing(contas.con()) as c:
        uid = _inserir(c, nome, email, senha, conta_id, "dono")
        c.execute("UPDATE contas SET dono_id=? WHERE id=?", (uid, conta_id))
        c.commit()
        return _um(c, uid)


def _checar_tentativas(ip):
    with _LOCK:
        recentes = [t for t in _FALHAS.get(ip, []) if time.time() - t < JANELA]
        _FALHAS[ip] = recentes
        if len(recentes) >= MAX_FALHAS:
            raise ErroAuth("Muitas tentativas erradas. Espere 10 minutos e tente de novo.", 429)


def _falhou(ip):
    with _LOCK:
        _FALHAS.setdefault(ip, []).append(time.time())


def entrar(email, senha, ip):
    """Confere e-mail e senha e abre uma sessão. Devolve (token, usuário)."""
    _checar_tentativas(ip)
    email = (email or "").strip().lower()
    with closing(contas.con()) as c:
        row = c.execute(SELECT.replace("SELECT ", "SELECT u.senha_hash, ", 1) + " WHERE u.email=?", (email,)).fetchone()
        ok = conferir_senha(senha or "", row[0] if row else _HASH_FALSO)
        if not row or not ok:
            _falhou(ip)
            raise ErroAuth("E-mail ou senha incorretos.", 401)
        u = _publico(row[1:])
        if u["status"] == "pendente":
            raise ErroAuth("Seu acesso aguarda a aprovação do administrador.", 403)
        if u["status"] == "bloqueado":
            raise ErroAuth("Este usuário está bloqueado. Fale com o responsável pela sua empresa.", 403)
        if u["conta"]["status"] == "pendente":
            raise ErroAuth("A conta da sua empresa foi criada e aguarda aprovação. Avisaremos quando liberar.", 403)
        if u["conta"]["status"] != "ativa":
            raise ErroAuth("A conta da sua empresa está bloqueada. Fale com o suporte.", 403)
        token = secrets.token_urlsafe(32)
        c.execute("INSERT INTO sessoes(token_hash,usuario_id,criado,expira) VALUES(?,?,?,?)",
                  (_hash_token(token), u["id"], _agora(), (datetime.now() + timedelta(days=SESSAO_DIAS)).isoformat(timespec="seconds")))
        c.execute("UPDATE usuarios SET ultimo_login=? WHERE id=?", (_agora(), u["id"]))
        c.execute("DELETE FROM sessoes WHERE expira < ?", (_agora(),))
        c.commit()
    with _LOCK:
        _FALHAS.pop(ip, None)
    return token, {**u, "ultimo_login": _agora()}


def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def usuario_da_sessao(token):
    """Usuário dono da sessão, ou None se ela não existe, expirou, ou o usuário/conta não está mais ativo."""
    if not token:
        return None
    with closing(contas.con()) as c:
        row = c.execute(SELECT + " JOIN sessoes s ON s.usuario_id=u.id WHERE s.token_hash=? AND s.expira>=?",
                        (_hash_token(token), _agora())).fetchone()
    if not row:
        return None
    u = _publico(row)
    return u if u["status"] == "ativo" and u["conta"]["status"] == "ativa" else None


def sair(token):
    if token:
        with closing(contas.con()) as c:
            c.execute("DELETE FROM sessoes WHERE token_hash=?", (_hash_token(token),))
            c.commit()


def trocar_minha_senha(usuario_id, atual, nova, token_atual):
    """O próprio usuário troca a senha. Encerra as outras sessões dele (mantém a atual)."""
    if not isinstance(nova, str) or not SENHA_MIN <= len(nova) <= 200:
        raise ErroAuth(f"A nova senha precisa ter pelo menos {SENHA_MIN} caracteres.")
    with closing(contas.con()) as c:
        row = c.execute("SELECT senha_hash FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
        if not row or not conferir_senha(atual or "", row[0]):
            raise ErroAuth("A senha atual está incorreta.", 403)
        if conferir_senha(nova, row[0]):
            raise ErroAuth("A nova senha precisa ser diferente da atual.")
        c.execute("UPDATE usuarios SET senha_hash=?, trocar_senha=0 WHERE id=?", (hash_senha(nova), usuario_id))
        c.execute("DELETE FROM sessoes WHERE usuario_id=? AND token_hash<>?", (usuario_id, _hash_token(token_atual or "")))
        c.commit()


def senha_temporaria():
    """Senha fácil de ditar: 3 blocos de 4, sem letras/números que se confundem (0/O, 1/l/I)."""
    alfabeto = "abcdefghjkmnpqrstuvwxyz23456789"
    return "-".join("".join(secrets.choice(alfabeto) for _ in range(4)) for _ in range(3))


def _aplicar(c, alvo_id, acao, senha, proprio):
    """Ações comuns ao admin da plataforma e ao dono da conta. Devolve extras da resposta."""
    if acao in ("aprovar", "desbloquear"):
        c.execute("UPDATE usuarios SET status='ativo' WHERE id=?", (alvo_id,))
    elif acao == "bloquear":
        c.execute("UPDATE usuarios SET status='bloqueado' WHERE id=?", (alvo_id,))
        c.execute("DELETE FROM sessoes WHERE usuario_id=?", (alvo_id,))
    elif acao == "trocar_senha":
        nova = (senha or "").strip() or senha_temporaria()
        if not SENHA_MIN <= len(nova) <= 200:
            raise ErroAuth(f"A senha precisa ter pelo menos {SENHA_MIN} caracteres.")
        # a pessoa troca no próximo acesso; as sessões abertas dela são encerradas (menos as de quem trocou a própria)
        c.execute("UPDATE usuarios SET senha_hash=?, trocar_senha=? WHERE id=?", (hash_senha(nova), int(not proprio), alvo_id))
        if not proprio:
            c.execute("DELETE FROM sessoes WHERE usuario_id=?", (alvo_id,))
        return {"senha_temporaria": nova}
    elif acao == "excluir":
        c.execute("DELETE FROM sessoes WHERE usuario_id=?", (alvo_id,))
        c.execute("DELETE FROM usuarios WHERE id=?", (alvo_id,))
    return {}


# ---- administrador da plataforma (o server.py confere papel == 'admin') ----

def listar_usuarios():
    with closing(contas.con()) as c:
        rows = c.execute(SELECT + " ORDER BY u.status='pendente' DESC, k.nome COLLATE NOCASE, u.papel_conta='dono' DESC, u.nome COLLATE NOCASE").fetchall()
    return [_publico(r) for r in rows]


def _admins_ativos(c, menos=None):
    return c.execute("SELECT COUNT(*) FROM usuarios WHERE papel='admin' AND status='ativo' AND id<>?", (menos or 0,)).fetchone()[0]


def administrar(admin_id, alvo_id, acao, senha=None):
    """Ação do administrador da plataforma sobre qualquer usuário."""
    if acao not in ("aprovar", "bloquear", "desbloquear", "tornar_admin", "tornar_usuario", "trocar_senha", "excluir"):
        raise ErroAuth("Ação inválida.")
    try:
        alvo_id = int(alvo_id)
    except (TypeError, ValueError):
        raise ErroAuth("Usuário inválido.")
    with closing(contas.con()) as c:
        u = _um(c, alvo_id)
        if not u:
            raise ErroAuth("Usuário não encontrado.", 404)
        proprio = alvo_id == admin_id
        if proprio and acao in ("bloquear", "tornar_usuario", "excluir"):
            raise ErroAuth("Você não pode fazer isso com a sua própria conta.", 409)
        if (acao in ("bloquear", "tornar_usuario", "excluir") and u["papel"] == "admin" and u["status"] == "ativo"
                and _admins_ativos(c, menos=alvo_id) == 0):
            raise ErroAuth("Este é o único administrador ativo. Torne outra pessoa admin antes.", 409)
        if acao == "excluir" and u["papel_conta"] == "dono":
            raise ErroAuth("Esta pessoa é a dona da conta da empresa. Para removê-la, exclua a conta na aba Clientes.", 409)
        if acao in ("tornar_admin", "tornar_usuario"):
            c.execute("UPDATE usuarios SET papel=? WHERE id=?", ("admin" if acao == "tornar_admin" else "usuario", alvo_id))
            extra = {}
        else:
            extra = _aplicar(c, alvo_id, acao, senha, proprio)
        c.commit()
        return {} if acao == "excluir" else {"usuario": _um(c, alvo_id), **extra}


def admin_criar_conta(empresa, plano, nome, email, senha=None):
    """O admin cria a conta de um cliente já ativa, com o dono e uma senha temporária."""
    if not planos.valido(plano):
        raise ErroAuth("Plano inválido.")
    nova = (senha or "").strip() or senha_temporaria()
    nome, email = _validar(nome, email, nova)
    with closing(contas.con()) as c:
        _email_livre(c, email)
    conta_id = _conta_nova(None, empresa, plano, "ativa")
    with closing(contas.con()) as c:
        uid = _inserir(c, nome, email, nova, conta_id, "dono", trocar=True)
        c.execute("UPDATE contas SET dono_id=? WHERE id=?", (uid, conta_id))
        c.commit()
        return {"usuario": _um(c, uid), "senha_temporaria": nova}


# ---- equipe da conta (o dono gerencia; membros só veem) ----

def equipe(usuario):
    conta_id = usuario["conta"]["id"]
    with closing(contas.con()) as c:
        rows = c.execute(SELECT + " WHERE u.conta_id=? ORDER BY u.papel_conta='dono' DESC, u.nome COLLATE NOCASE", (conta_id,)).fetchall()
    p = planos.PLANOS.get(usuario["conta"]["plano"], {})
    return {"conta": usuario["conta"], "plano": dict(p, id=usuario["conta"]["plano"]),
            "membros": [_publico(r) for r in rows], "eu": usuario["id"], "sou_dono": usuario["papel_conta"] == "dono"}


def _so_dono(usuario):
    if usuario["papel_conta"] != "dono":
        raise ErroAuth("Só o dono da conta pode gerenciar a equipe.", 403)


def equipe_criar(usuario, nome, email, senha=None):
    _so_dono(usuario)
    conta = usuario["conta"]
    limite = planos.PLANOS.get(conta["plano"], {}).get("usuarios", 1)
    nova = (senha or "").strip() or senha_temporaria()
    nome, email = _validar(nome, email, nova)
    with closing(contas.con()) as c:
        if c.execute("SELECT COUNT(*) FROM usuarios WHERE conta_id=?", (conta["id"],)).fetchone()[0] >= limite:
            raise ErroAuth(f"O plano {conta['plano_nome']} permite {limite} usuário(s). Para adicionar mais pessoas, "
                           "mude de plano ou contrate usuários extras.", 409)
        _email_livre(c, email)
        uid = _inserir(c, nome, email, nova, conta["id"], "membro", trocar=True)
        c.commit()
        return {"usuario": _um(c, uid), "senha_temporaria": nova}


def equipe_acao(usuario, alvo_id, acao, senha=None):
    _so_dono(usuario)
    if acao not in ("aprovar", "bloquear", "desbloquear", "trocar_senha", "excluir"):
        raise ErroAuth("Ação inválida.")
    try:
        alvo_id = int(alvo_id)
    except (TypeError, ValueError):
        raise ErroAuth("Usuário inválido.")
    with closing(contas.con()) as c:
        alvo = _um(c, alvo_id)
        if not alvo or alvo["conta"]["id"] != usuario["conta"]["id"]:
            raise ErroAuth("Usuário não encontrado.", 404)  # nunca mexe em gente de outra empresa
        proprio = alvo_id == usuario["id"]
        if proprio and acao != "trocar_senha":
            raise ErroAuth("Você não pode fazer isso com a sua própria conta.", 409)
        if not proprio and (alvo["papel_conta"] == "dono" or alvo["papel"] == "admin"):
            raise ErroAuth("Não é possível alterar esta pessoa.", 403)
        extra = _aplicar(c, alvo_id, acao, senha, proprio)
        c.commit()
        return {} if acao == "excluir" else {"usuario": _um(c, alvo_id), **extra}
