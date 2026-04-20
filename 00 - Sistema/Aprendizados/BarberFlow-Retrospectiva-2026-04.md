---
tópico: Projeto BarberFlow
tipo: Aprendizado Técnico / Retrospectiva
tags: [firebase, cloud-run, react, backend, postgres, ux]
data: 2026-04-16
---

# ✂️ BarberFlow: Ciclo de Desenvolvimento e Deploy

Resumo dos aprendizados fundamentais e decisões de arquitetura tomadas durante a fase de otimização mobile e deploy em produção via Firebase.

## 🏗️ Arquitetura e Backend (Cloud Run / Functions Gen 2)

### 1. Desafio do Healthcheck em Serverless
Ao converter um monolito Express para Firebase Functions (Gen 2/Cloud Run), o processo de boot deve ser extremamente rápido.
- **Problema**: O código tentava inicializar o banco de dados (`initSchema`) e conectar ao Postgres imediatamente no carregamento do módulo. Se o banco demorasse, o container "falhava" no healthcheck (Erro 403/Port 8080).
- **Solução**: Implementamos **Lazy Initialization**. O servidor sobe instantaneamente, e o banco só tenta sincronizar no primeiro "middleware" de requisição ou via promessa não bloqueante.

### 2. Resiliência com Imports Dinâmicos
Para permitir que o mesmo código rode localmente (com SQLite) e em produção (com Postgres) sem erros de dependência ausente:
- Utilizamos `await import('better-sqlite3')` dentro do bloco condicional. Isso evita que o Node.js tente carregar o driver de SQLite em produção (onde ele não está instalado), eliminando crashes de carregamento.

## 📱 Frontend e UX (Aesthetics & Flow)

### 1. Inversão de Fluxo (Barbeiro Primeiro)
- **Insight**: Em serviços de cuidado pessoal, o vínculo com o profissional costuma ser maior que com o serviço específico.
- **Mudança**: Alteramos o fluxo de agendamento para identificar o Barbeiro **antes** do Serviço. Isso permite perguntas personalizadas ("O que vamos fazer com o João?") e melhora a percepção de atendimento exclusivo.

### 2. Admin em Dispositivos Móveis
- Tabelas com muitos dados em mobile devem usar `overflow-x: auto` e `white-space: nowrap` nas células para evitar colapso de layout.
- O uso de Sidebars com overlay (`sidebar-open`) é essencial para manter o foco em telas pequenas.

## 🚀 Infraestrutura de Deploy

- **Estratégia**: Pivotamos do *App Hosting* (dependente de conexões CI/CD/GitHub) para um **Deploy Direto via CLI** (`firebase-tools`).
- **Benefício**: Maior agilidade na resolução de problemas de permissão (IAM) e variáveis de ambiente, mantendo o controle total no terminal do desenvolvedor.

---
> [!TIP]
> **Próxima vez**: Para projetos semelhantes, comece com a estrutura de `initSchema` desacoplada do boot principal para evitar problemas de cold-start em Cloud Run desde o dia 1.
