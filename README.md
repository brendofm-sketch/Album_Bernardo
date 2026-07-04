# Album Copa 2026 - imagens externas

Este projeto usa imagens locais no padrao:

```text
figurinhas/COD_00.webp
```

Exemplos:

```text
figurinhas/BRA_01.webp
figurinhas/BRA_02.webp
figurinhas/ARG_01.webp
figurinhas/FRA_10.webp
```

O arquivo `album_copa_2026_premium_imagens_externas.html` ja procura as imagens em `figurinhas/` com extensao `.webp`. Depois que as imagens forem geradas, o album funciona offline abrindo o HTML no navegador.

## Usar como app no tablet

O projeto tambem funciona como PWA instalavel. Para usar em um tablet na mesma rede do computador:

```bash
python start_tablet_server.py
```

Depois abra no tablet o endereco mostrado no terminal, parecido com:

```text
http://192.168.0.10:8765/album_copa_2026_premium_imagens_externas.html
```

No Android/Chrome, use o botao `Instalar` quando aparecer. No iPad/Safari, use `Compartilhar > Adicionar a Tela de Inicio`. Depois da primeira abertura, o app usa cache local para carregar a interface e as imagens ja acessadas.

## Publicar no GitHub Pages

O projeto ja tem `index.html`, `.nojekyll`, `manifest.webmanifest` e `sw.js` preparados para GitHub Pages. A pasta `figurinhas/` e `bandeiras/` deve ser enviada junto.

Arquivos locais pesados como PDFs, recortes de extracao e auditorias ficam fora do Git pelo `.gitignore`.

Passo a passo:

```bash
git init
git add .
git commit -m "Publica album digital"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git
git push -u origin main
```

Depois, no GitHub:

1. Abra o repositorio.
2. Va em `Settings`.
3. Entre em `Pages`.
4. Em `Build and deployment`, escolha `Deploy from a branch`.
5. Em `Branch`, escolha `main` e pasta `/root`.
6. Salve.

O link ficara parecido com:

```text
https://SEU_USUARIO.github.io/NOME_DO_REPOSITORIO/
```

As marcacoes do album continuam salvas no navegador de cada aparelho. Para levar o progresso de um aparelho para outro, use `Backup` e `Importar JSON`.

As bandeiras ficam em:

```text
bandeiras/COD.svg
```

Para baixar ou atualizar as bandeiras locais:

```bash
python fetch_bandeiras.py
```

## Recortar figurinhas do PDF

O arquivo `TODAS LAS FIGURITAS EN PDF (4).pdf` pode ser usado como primeira fonte das imagens. O script `extract_pdf_figurinhas.py` renderiza cada pagina em alta resolucao, detecta a grade 4x4, recorta as figurinhas, tenta casar pelo OCR com os nomes/codigos do HTML e salva os matches em:

```text
figurinhas/COD_00.webp
```

Para rodar:

```bash
python extract_pdf_figurinhas.py --threshold 0.86
```

O script tambem gera `pdf_recortes/` com os recortes originais e `pdf_recortes_manifest.csv` com pagina, linha, coluna, texto lido e codigo encontrado. Escudos cromados e alguns cards de elenco podem usar overrides de posicao no proprio script quando o OCR nao le bem.

Quando o arquivo `album 101 paginas completo.pdf` estiver na pasta, o extrator usa esse PDF como fonte principal por estar na ordem do album. Nesse modo ele grava os recortes em `pdf_101_recortes/` e o relatorio em `pdf_101_recortes_manifest.csv`. Cards de elenco do tipo `WE ARE` sao tratados como a figurinha `COD_13`.

## Figurinhas especiais FWC e CC

O controle tambem inclui grupos especiais fora das selecoes:

- `FWC_00.webp` ate `FWC_19.webp`: FIFA World Cup History.
- `CC_01.webp` ate `CC_14.webp`: figurinhas especiais da Coca-Cola.

Para extrair essas imagens do PDF principal:

```bash
python extract_special_figurinhas.py
```

O HTML conta esses grupos no total geral, nas estatisticas, na lista de faltantes, nas repetidas e na tela de controle.

Dependencias usadas por esse fluxo:

```bash
python -m pip install pymupdf easyocr opencv-python-headless pillow
```

## Checklist real do album

O HTML foi atualizado com nomes reais, numeros e tipos de figurinha a partir do checklist publico do Scanini:

- Album: https://scanini.app/albums/world-cup-2026
- Exemplo Brasil: https://scanini.app/teams/brazil

O Scanini informa que cada selecao tem 20 figurinhas: `1` e o escudo/logo do time, `13` e a foto do elenco, e as demais sao retratos de jogadores. O projeto usa esses nomes/codigos apenas como referencia de controle de colecao.

Para atualizar o HTML de novo a partir do checklist:

```bash
python update_checklist_from_scanini.py
```

Isso tambem gera `checklist_scanini_2026.json` como registro local da fonte usada.

## Gerar imagens simples locais

Requisitos:

- Python 3
- Pillow

Se precisar instalar o Pillow:

```bash
python -m pip install pillow
```

Para gerar todas as figurinhas faltantes:

```bash
python generate_figurinhas.py
```

O script:

- le os paises, codigos, nomes, numeros e tipos diretamente do HTML;
- salva cada arte como `figurinhas/COD_00.webp`;
- pula imagens que ja existem;
- cria `figurinhas/prompts_manifest.json` com o prompt usado para cada item.

Para sobrescrever todas as imagens:

```bash
python generate_figurinhas.py --force
```

Para testar gerando poucas imagens:

```bash
python generate_figurinhas.py --limit 10
```

## Gerar imagens com IA e foto de referencia

Para gerar figurinhas realmente ilustradas por IA, com cada jogador reconhecivel a partir de uma foto de referencia:

1. Busque referencias abertas:

```bash
python fetch_referencias_abertas.py --team BRA
```

Ou para tentar todos os jogadores:

```bash
python fetch_referencias_abertas.py --delay 0.05
```

O script cria:

```text
referencias/referencias_jogadores.csv
referencias/COD_00.jpg
```

Revise o CSV antes de gerar. Ele registra caminho, URL, pagina e licenca quando a API retorna esses dados. Nem todo jogador tera foto aberta encontrada automaticamente.

2. Defina sua chave da OpenAI no ambiente:

```bash
set OPENAI_API_KEY=sua_chave_aqui
```

No PowerShell:

```powershell
$env:OPENAI_API_KEY="sua_chave_aqui"
```

3. Gere as figurinhas por IA:

```bash
python generate_figurinhas_ia.py --team BRA --force
```

Para gerar somente algumas, bom para testar custo/qualidade:

```bash
python generate_figurinhas_ia.py --team BRA --limit 3 --force
```

Para permitir geracao mesmo quando nao houver foto de referencia:

```bash
python generate_figurinhas_ia.py --team BRA --include-no-reference --force
```

O script salva tudo no mesmo padrao que o HTML ja usa:

```text
figurinhas/COD_00.webp
```

Importante: transformar foto em desenho nao remove automaticamente direitos autorais, licencas de imagem ou direitos de personalidade. Para um controle familiar/educativo, prefira fotos abertas ou imagens que voce tem permissao para usar. O prompt evita copia fotografica, marcas, patrocinadores, escudos oficiais e layout oficial da Panini.

## Usar fotos de referencia sem API

Se voce nao tiver API da OpenAI, ainda pode montar figurinhas locais com as fotos baixadas em `referencias/`. Isso nao transforma em desenho; monta um card local com codigo, nome e posicao:

```bash
python generate_figurinhas_referencias.py --team BRA --force
```

Fluxo recomendado por selecao:

```bash
python fetch_referencias_abertas.py --team BRA
python generate_figurinhas_referencias.py --team BRA --force
```

Para o Brasil, a primeira fonte recomendada agora e a pagina oficial de elenco da FIFA:

```bash
python fetch_fifa_brazil_refs.py
python generate_figurinhas_referencias.py --team BRA --force
```

Esse script usa a API publica carregada por:

```text
https://www.fifa.com/pt/tournaments/mens/worldcup/canadamexicousa2026/teams/brazil/squad
```

Ele baixa as fotos encontradas no FIFA Digital Hub, converte para JPG local em `referencias/`, atualiza `referencias/referencias_jogadores.csv` e preserva as referencias existentes dos jogadores do checklist que nao aparecem no elenco atual da FIFA.

Para tentar todas as selecoes, rode em lotes ou uma selecao por vez. A Wikimedia pode bloquear temporariamente muitas buscas/downloads seguidos:

```bash
python fetch_referencias_abertas.py --team ARG
python generate_figurinhas_referencias.py --team ARG --force
```

Para regenerar todas as 960 figurinhas usando as referencias ja baixadas:

```bash
python normalize_positions.py
python generate_figurinhas_referencias.py --format webp --force
```

Se a busca automatica nao encontrar um jogador, coloque a imagem correta em `referencias/COD_00.jpg` e rode o gerador novamente.

O script `normalize_positions.py` usa as posicoes vindas da FIFA quando disponiveis e completa os poucos casos restantes pela ordem de grupos do checklist do album.

Para salvar tambem em JPG:

```bash
python generate_figurinhas_referencias.py --team BRA --format both --force
```

Esse modo garante que o codigo da figurinha apareca no card, como `BRA02`, `BRA03`, `FRA10`.

As fontes sao registradas em `referencias/referencias_jogadores.csv`. O script prioriza imagens abertas da Wikipedia/Wikimedia. Quando uma foto vem de fonte oficial de clube ou site similar, a licenca fica marcada como desconhecida para revisao.

Tratamento por tipo:

- `badge`: usa uma imagem de logo/entidade quando houver referencia local. Exemplo: `BRA01` usa o logo da CBF registrado no CSV.
- `player`: usa o retrato em `referencias/COD_00.jpg` ou `.png`.
- `squad`: monta uma formacao em campo com os retratos disponiveis da selecao. Exemplo: `BRA13` e gerado como elenco posicionado no gramado.

O site da FIFA pode ser usado como fonte manual quando a URL direta da imagem estiver disponivel, mas a pagina publica de noticias/elenco e renderizada por JavaScript e nem sempre expoe as imagens no HTML baixado pelo script. Nesses casos, coloque manualmente a imagem em `referencias/COD_00.jpg` ou registre a URL no CSV antes de regenerar.

Nao use imagem da figurinha oficial como fallback, porque isso copia diretamente a arte/produto protegido.

## Gerar manualmente no ChatGPT Plus

O ChatGPT Plus inclui geracao de imagens, mas a API nao esta incluida no plano Plus; a API e cobrada separadamente. No Plus, o caminho pratico e gerar em lotes pequenos no proprio chat e baixar as imagens manualmente.

Prompt sugerido para cada jogador:

```text
Use a foto anexada apenas como referencia visual para criar uma ilustracao original em estilo figurinha esportiva digital premium.
Jogador: {NOME}
Selecao: {PAIS}
Codigo da figurinha: {CODIGO}
Posicao: {POSICAO}

Criar retrato de busto reconhecivel em estilo cartoon 3D/editorial, fundo esportivo abstrato, uniforme inspirado nas cores da selecao, sem logotipos oficiais, sem marcas, sem patrocinadores, sem copiar layout oficial da Panini. Card vertical de figurinha, acabamento premium, luz de estudio.
Incluir o codigo "{CODIGO}" pequeno no canto superior esquerdo e o nome "{NOME}" na tarja inferior.
Formato vertical, alta qualidade, sem marca d'agua.
```

Depois de baixar a imagem, salve com o nome esperado pelo HTML:

```text
figurinhas/BRA_03.webp
```

Se baixar em JPEG, use o script local para converter ou altere `IMAGE_EXT` no HTML para `.jpg`.

## Diretrizes das artes

As imagens geradas sao ilustracoes originais em estilo figurinha esportiva digital premium, com linguagem de figurinha colecionavel classica: card vertical, moldura branca, brilho de impressao, retrato central e fundo esportivo. Elas usam cores inspiradas nas selecoes e variam por pais, numero e tipo:

- `badge`: logo/entidade quando voce fornecer uma referencia local permitida; sem referencia, simbolo generico com escudo geometrico, bola e formas esportivas.
- `player`: busto ilustrado; no fluxo com IA, usa foto aberta como referencia para representar o jogador sem copiar a foto.
- `squad`: elenco em campo; no fluxo local, uma formacao gerada a partir das fotos de referencia da selecao.

Nao use imagens oficiais da Panini, layouts oficiais, escudos oficiais, logotipos de selecoes, marcas protegidas ou retratos reais redesenhados. A ideia e manter apenas convencoes genericas de album de futebol, sem copiar identidade visual proprietaria.

## Atualizar imagens manualmente

Voce pode substituir qualquer arquivo em `figurinhas/` mantendo exatamente o mesmo nome. Por exemplo, para trocar a figurinha 10 da Franca, substitua:

```text
figurinhas/FRA_10.webp
```

Depois, basta recarregar o HTML no navegador.

## Visualizacao ampliada

No HTML, clicar em uma figurinha abre uma pre-visualizacao grande da imagem. Use os botoes dentro da pre-visualizacao para marcar como tenho, adicionar repetida ou fechar.
