# Tutorial: Recuperação da tela via cartão SD (duas fases)

> Procedimento baseado no Readme oficial do pacote Creality
> (`docs/Readme_firmware_update_CN_EN.txt`) e nas análises §2.6/§2.7 do
> `plano-recuperacao-completo.md`. É o único caminho que pode resolver o
> brick **sem solda**.

## O que você vai precisar

- Cartão microSD (o slot é da própria tela) + leitora
- Os arquivos do repositório:
  - `dcboot.bin` — fase 1 (regrava a área de boot)
  - `firmware.zlib` — fase 2 (regrava o OS)
  - `private/` — fase 2 (assets DACAI)
  - `DWIN_SET/` — fase 2 (assets DWIN; a tela escolhe sozinha a pasta da sua variante)

## ⚠️ Antes de começar

- **Confirme que este pacote é compatível com a S1 Pro.** O brick foi
  causado por pacote do modelo errado — não repita o erro.
- A **fase 1 é a mais crítica**: ela regrava a área de boot. Não
  interrompa a impressora durante o processo.
- Se possível, faça antes um dump da flash atual via FEL ou clipe
  SOIC-8 (ver `backup-flash-nixos.md`) para ter um "estado antes".

---

## Passo 0 — Formatar o cartão em FAT32 (unidade de alocação 4096)

O Readme oficial exige alocação de 4096 bytes. No NixOS:

```bash
# 1. Identifique o cartão (confira pelo tamanho — ex.: /dev/sdb)
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT

# 2. Desmonte se estiver montado
sudo umount /dev/sdb?* 2>/dev/null

# 3. Formate
sudo mkfs.fat -F 32 -S 4096 -n SCREEN /dev/sdb1
```

Se `mkfs.fat` não existir: `nix-shell -p dosfstools`.

No Windows: formatar com "Tamanho da unidade de alocação" = **4096**.

## Passo 1 — Fase 1: regravar a área de boot

1. Copie **apenas** o `dcboot.bin` para a raiz do cartão:

   ```bash
   cp dcboot.bin /run/media/$USER/SCREEN/
   ```

2. Ejete com segurança e desligue a impressora.
3. Remova a tela do suporte (4 parafusos traseiros), mantendo os cabos
   conectados.
4. Insira o cartão no slot microSD da parte de trás da tela.
5. Ligue a impressora e aguarde. A tela pode mostrar progresso ou ficar
   preta por alguns minutos. **Não desligue.**
6. Aguarde ao menos 5 minutos após qualquer sinal de término.

## Passo 2 — Fase 2: regravar OS + assets

1. Desligue a impressora e remova o cartão.
2. No computador, **apague o `dcboot.bin`** do cartão.
3. Copie para a raiz do cartão:

   ```bash
   cp firmware.zlib /run/media/$USER/SCREEN/
   cp -r private DWIN_SET /run/media/$USER/SCREEN/
   ```

4. Ejete, reinsira na tela e ligue a impressora.
5. Aguarde o processo terminar (na variante DACAI aparece fundo azul
   com texto rolando e porcentagem; na DWIN aparece `END !`).
6. Desligue, remova o cartão (**importante**: com o cartão inserido a
   tela tenta atualizar a cada boot).

## Passo 3 — Verificar

- Ligue sem o cartão e veja se a tela inicia normalmente (pode demorar
  na logo da Creality).
- Confira a versão na página *About* da tela.

## Se não funcionar

| Sintoma | Possível causa | Próximo passo |
|---|---|---|
| Nada muda, só bipe | Boot não executou o updater | Conferir se o cartão ficou com alocação 4096; tentar outro cartão (menor, ≤32 GB); conferir formato do `dcboot.bin` (sha256) |
| Tela piorou | Pacote incompatível com a variante | Interromper tentativas SD; seguir para Frente A (FEL via USB, §4.1 do plano) |
| Progresso aparece mas falha | Cartão lento/defeituoso | Tentar outro cartão classe 10 |

Em qualquer caso de falha, o caminho garantido continua sendo gravar
uma imagem completa de 16 MB via FEL/clipe — ver
`plano-recuperacao-completo.md` §4 e §6.
