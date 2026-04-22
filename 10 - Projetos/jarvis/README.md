# Jarvis Frontend Generation

Pipeline deterministico de geracao de frontend para a Fase 1:

1. Intent Analyzer
2. PageSchema Builder
3. Design System Resolver
4. Frontend Composer
5. Validator

## Setup

```bash
cd "10 - Projetos/jarvis"
npm install
npm run install-browsers
```

## Gerar pagina

```bash
npm run generate-page -- --prompt "dashboard de telemetria de agentes"
```

Esse comando agora gera `preview.html` no diretório de artefatos, pronto para validação visual real.

## Revisar pagina

```bash
npm run review-page -- --page .artifacts/pages/<id>/generated-page.tsx
```

## Testar pagina

```bash
npm run test-page -- --page .artifacts/pages/<id>/generated-page.tsx
```

Para criar baseline inicial de snapshots:

```bash
npm run test-page -- --page .artifacts/pages/<id>/generated-page.tsx --update-baseline
```
