# 🚀 System Prompt Generator (Dinâmico)

Use este guia como uma "receita" para fornecer o contexto ideal para qualquer IA, garantindo que ela saiba quem você é e como você trabalha, sem desperdiçar tokens com informações irrelevantes.

---

## 🛠️ O Prompt de Inicialização (Bootstrap)

Quando começar uma nova conversa com uma IA, copie e cole este bloco (substituindo o conteúdo entre chaves pelo conteúdo da sua nota no Obsidian):

```text
Você é minha extensão cognitiva operando sob o framework do meu Segundo Cérebro. 
Para esta sessão, assuma a Persona: {Copia o conteúdo da nota em '01 - Personas/Nome da Persona'}

DIRETRIZES DE EFICIÊNCIA:
1. Respeite as regras de estilo em meu 'Self-Correction Log'.
2. Use o contexto comprimido (TL;DR) das notas de referência.
3. Se não encontrar uma informação, peça o caminho da nota em '30 - Recursos'.
```

---

## 📉 Como reduzir o consumo de tokens na prática

1. **Injeção Cirúrgica**: Em vez de colar 10 notas, cole apenas o resumo YAML e o `## TL;DR` das notas que não são o foco principal.
2. **Uso de IDs**: Refira-se a projetos e pessoas por nomes únicos ou IDs definidos no Obsidian. Isso ajuda a IA a manter a consistência sem precisar de re-explicações.
3. **Poda de Histórico**: Ao perceber que a conversa está ficando longa e "alucinando", peça à IA para: *"Resuma nosso progresso técnico até agora e reinicie o buffer de contexto usando apenas este resumo"*.

---

## 🔄 Automação com Plugins
Se estiver usando plugins como o **Text Generator** ou **Copilot (Obsidian)**, utilize as variáveis:
- `{{selectedText}}` para contexto imediato.
- `{{persona_context}}` (custom code) para injetar as diretrizes da persona ativa.
