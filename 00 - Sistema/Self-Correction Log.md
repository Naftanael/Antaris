# 🧠 Self-Correction Log (Memória de Erros e Acertos)

Este documento serve como a base de dados para o afinamento do seu Segundo Cérebro. Ele registra falhas de contexto e lógica cometidas pelas IAs para evitar que ocorram novamente.

---

## 📈 Tabela de Aprendizado Ativo

| Data | Persona | Erro Identificado | Correção Técnica Aplicada | Status |
| :--- | :--- | :--- | :--- | :--- |
| 2026-04-15 | O Arquiteto | Falha em considerar custo de tokens na injeção. | Criada estruturação L1/L2/L3. | ✅ Resolvido |
| 2026-04-16 | O Engenheiro | Crash de Healthcheck em Cloud Run (Gen 2). | Implementado Lazy Init no Db e Server. | ✅ Resolvido |

---

## 🛠️ Padrões de Recorrência
*Consolide aqui os erros que acontecem mais de uma vez para criar uma "Regra de Ouro".*

1. **Regra #1:** Nunca envie o histórico completo de chats se a nota de resumo (TL;DR) estiver disponível.
2. **Regra #2:** Priorize o YAML das Personas sobre as instruções genéricas de sistema.

---

## 📋 Como alimentar este Log
Use o arquivo `[[Template - Feedback Loop IA]]` para gerar uma nova entrada sempre que notar uma imprecisão.
