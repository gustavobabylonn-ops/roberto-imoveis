#!/usr/bin/env python3
"""Gera uma página própria para cada imóvel (ex.: /gaia-cabral/).

Cada página é uma cópia do index.html que já abre direto no imóvel e tem
título, descrição e foto próprios para a prévia do WhatsApp e para o Google.
Rode de novo sempre que o index.html mudar:

    python3 ferramentas/gerar_paginas.py            # todos os imóveis
    python3 ferramentas/gerar_paginas.py gaia-cabral  # só alguns
"""
import html
import pathlib
import re
import sys

SITE = "https://robertoimoveiscwb.com.br"
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def texto(trecho):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", trecho)).split())


def achar(padrao, bloco):
    m = re.search(padrao, bloco, re.S)
    return texto(m.group(1)) if m else ""


def cartoes(pagina):
    for m in re.finditer(r'<article class="feature" data-id="([^"]+)".*?</article>', pagina, re.S):
        bloco = m.group(0)
        yield {
            "id": m.group(1),
            "nome": achar(r"<h3>(.*?)</h3>", bloco),
            "local": achar(r'<span class="tag">(.*?)</span>', bloco).replace(" · ", ", "),
            "sub": achar(r'<p class="sub">(.*?)</p>', bloco),
            "preco": achar(r'<div class="price-row[^"]*">(.*?)</div>', bloco),
            "foto": re.search(r'class="g-main" src="([^"]+)"', bloco).group(1),
        }


def gerar(pagina, c):
    url = f"{SITE}/{c['id']}/"
    titulo = f"{c['nome']} · {c['local']} | Roberto Imóveis"
    descricao = ". ".join(p for p in (c["sub"], c["preco"]) if p)
    e = lambda s: html.escape(s, quote=True)
    cabeca = (
        '<base href="../">'
        f"<title>{e(titulo)}</title>"
        f'<meta name="description" content="{e(descricao)}">'
        f'<link rel="canonical" href="{url}">'
        '<meta property="og:type" content="website">'
        '<meta property="og:locale" content="pt_BR">'
        '<meta property="og:site_name" content="Roberto Imóveis">'
        f'<meta property="og:title" content="{e(c["nome"] + " · " + c["local"])}">'
        f'<meta property="og:description" content="{e(descricao)}">'
        f'<meta property="og:image" content="{SITE}/{c["foto"]}">'
        f'<meta property="og:url" content="{url}">'
        '<meta name="twitter:card" content="summary_large_image">'
        # abre o imóvel assim que a página carrega
        f"<script>try{{if(!location.hash)history.replaceState(null,'',location.pathname+location.search+'#{c['id']}')}}catch(e){{}}</script>"
    )
    saida = pagina.replace("<html>", '<html lang="pt-BR">', 1)
    saida = re.sub(r"(<meta name=viewport[^>]*>)", lambda m: m.group(1) + cabeca, saida, count=1)
    saida = _sem_titulo_do_corpo(saida)
    destino = RAIZ / c["id"] / "index.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(saida, encoding="utf-8")
    return destino


def _sem_titulo_do_corpo(s):
    corte = s.index("</head>")
    return s[:corte] + re.sub(r"\n?<title>[^<]*</title>", "", s[corte:], count=1)


def main():
    pagina = (RAIZ / "index.html").read_text(encoding="utf-8")
    pedidos = set(sys.argv[1:])
    feitos = [gerar(pagina, c) for c in cartoes(pagina) if not pedidos or c["id"] in pedidos]
    for f in feitos:
        print("gerado:", f.relative_to(RAIZ))
    if not feitos:
        sys.exit("nenhum imóvel encontrado com esse id")


if __name__ == "__main__":
    main()
