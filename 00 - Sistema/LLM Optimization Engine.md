# LLM Optimization Engine: Arquitetura de Contexto Humano-IA

Esta documentação define os protocolos de engenharia para transformar o seu Obsidian em um ambiente de aprendizado para LLMs, visando reduzir o consumo de tokens e aumentar a precisão técnica.

---

## 1. Estratégia de Estratificação de Contexto

Para evitar o transbordamento do contexto (context overflow) e o custo excessivo de tokens, dividimos as informações em camadas:

| Camada | Conteúdo | Frequência de Acesso | Custo de Token |
| :--- | :--- | :--- | :--- |
| **L1: Hot Context** | Projetos ativos e logs das últimas 24h. | Alta | Alto (Integral) |
| **L2: Warm Context** | Referências técnicas e resumos de áreas. | Média | Médio (Summarized) |
| **L3: Cold Context** | Arquivo histórico e bibliotecas vastas. | Baixa | Baixo (RAG/Vetorizado) |

### Protocolo de Compressão
- Notas em `30 - Recursos` devem ser sumarizadas periodicamente para incluir uma seção `## TL;DR (Para IA)`.
- Isso reduz a carga de leitura da IA em até 70% sem perda de diretrizes críticas.

---

## 2. O Ciclo de Feedback (Learning Loop)

O sistema aprende através do monitoramento de discrepâncias entre a expectativa do usuário e a entrega da IA.

### Implementação do Log de Autocorreção
Toda vez que uma IA utilizada no fluxo cometer um erro lógico ou de estilo, o erro deve ser registrado em:
`[[00 - Sistema/Self-Correction Log]]`

**Campos de Registro:**
- **Trigger**: O prompt enviado.
- **Erro**: Onde a IA falhou (ex: "Uso excessivo de comentários no código").
- **Correção**: A instrução final que resolveu o problema.

---

## 3. Guia de System Prompting Dinâmico

Em vez de enviar um prompt fixo gigantesco, usamos o Obsidian para "montar" o prompt ideal:

```markdown
# Estrutura de Prompt Dinâmico
1. **Identidade**: {{Persona_YAML}}
2. **Contexto L1**: {{Note_Content}}
3. **Restrições de Estilo**: {{Self-Correction_Log_Latest_3}}
```

---

## 4. Métricas de Sucesso
- **Assertividade**: Porcentagem de tarefas concluídas sem necessidade de re-prompting.
- **Eficiência**: Média de tokens por resposta bem-sucedida.
- **Sincronia**: Redução na divergência de tom de voz entre a Persona e o usuário.
