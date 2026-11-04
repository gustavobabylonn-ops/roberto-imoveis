#!/usr/bin/env python3
"""Gera uma página própria para cada imóvel (ex.: /gaia-cabral/).

Cada página é uma cópia do index.html que já abre direto no imóvel e tem
título, descrição e foto próprios para a prévia do WhatsApp e para o Google.
Rode de novo sempre que o index.html mudar:

    python3 ferramentas/gerar_paginas.py            # todos os imóveis
    python3 ferramentas/gerar_paginas.py gaia-cabral  # só alguns

Rodando sem argumentos, também apaga a página de imóvel que saiu do site
e reescreve o sitemap.xml (lista de páginas para o Google).
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
            "preco": achar(r'<div class="price-row[^"]*"[^>]*>(.*?)</div>', bloco),
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
        f"<script>try{{var h=location.hash.slice(1);if(!h)history.replaceState(null,'',location.pathname+location.search+'#{c['id']}');"
        f"else if(h!=='{c['id']}')location.replace(new URL('../#'+h,location.href).href)}}catch(e){{}}</script>"
    )
    saida = pagina.replace("<html>", '<html lang="pt-BR">', 1)
    saida = re.sub(r"(<meta name=viewport[^>]*>)", lambda m: m.group(1) + cabeca, saida, count=1)
    saida = _sem_titulo_do_corpo(saida)
    # outro imóvel aberto daqui vai para a página principal, para o link não misturar os dois
    rodape = (
        "<script>window.addEventListener('hashchange',function(){var id=location.hash.slice(1);"
        f"if(id&&id!=='{c['id']}')location.replace(new URL('../#'+id,location.href).href)}})</script>"
    )
    corte = saida.rindex("</body>") if "</body>" in saida else len(saida)
    saida = saida[:corte] + rodape + saida[corte:]
    destino = RAIZ / c["id"] / "index.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(saida, encoding="utf-8")
    return destino


def _sem_titulo_do_corpo(s):
    corte = s.index("</head>")
    return s[:corte] + re.sub(r"\n?<title>[^<]*</title>", "", s[corte:], count=1)


def gerada_por_aqui(pasta):
    arq = pasta / "index.html"
    if not arq.is_file():
        return False
    inicio = arq.read_text(encoding="utf-8")[:4000]
    return '<base href="../">' in inicio and f'<link rel="canonical" href="{SITE}/{pasta.name}/">' in inicio


def limpar(ids):
    for pasta in sorted(RAIZ.iterdir()):
        if pasta.is_dir() and pasta.name not in ids and gerada_por_aqui(pasta):
            for f in pasta.iterdir():
                f.unlink()
            pasta.rmdir()
            print("removido:", pasta.name)


def sitemap(ids):
    urls = [f"{SITE}/"] + [f"{SITE}/{i}/" for i in ids]
    corpo = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (RAIZ / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{corpo}</urlset>\n',
        encoding="utf-8",
    )
    print("gerado: sitemap.xml")


def main():
    pagina = (RAIZ / "index.html").read_text(encoding="utf-8")
    pedidos = set(sys.argv[1:])
    todos = list(cartoes(pagina))
    feitos = [gerar(pagina, c) for c in todos if not pedidos or c["id"] in pedidos]
    for f in feitos:
        print("gerado:", f.relative_to(RAIZ))
    if not feitos:
        sys.exit("nenhum imóvel encontrado com esse id")
    if not pedidos:
        ids = [c["id"] for c in todos]
        limpar(set(ids))
        sitemap(ids)


if __name__ == "__main__":
    main()
