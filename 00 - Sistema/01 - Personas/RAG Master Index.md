# RAG Master Index - Matriz de Contexto Antaris

Este documento serve como o Ponto de Entrada (Entrypoint) para o sistema de Recuperação de Contexto (RAG) do Antaris. 

Sempre que uma nova tarefa de engenharia, arquitetura ou desenvolvimento for iniciada, o agente **DEVE** inspecionar o domínio da tarefa e carregar a Persona correspondente deste diretório para calibração antes de gerar a solução.

## 🗃️ Personas Disponíveis e Gatilhos de Ativação

| ID da Persona | Gatilhos (Keywords) | Arquivo Fonte |
| :--- | :--- | :--- |
| **Arquiteto Frontend** | `nextjs`, `react`, `typescript`, `ui`, `tailwind`, `zod`, `frontend` | `[[01 - Arquiteto Frontend]]` |
| **Engenheiro Python e IA** | `python`, `orquestrador`, `skill`, `backend`, `ast`, `automação` | `[[02 - Engenheiro de IA e Python]]` |
| **Executor DevOps** | `deploy`, `cloud run`, `firebase`, `docker`, `bash`, `servidor` | `[[03 - Executor Cloud e DevOps]]` |
| **Orquestrador Multi-Agente** | `multi-agent`, `delegate_task`, `sub-agentes`, `orquestração`, `claude-code`, `opencode` | `[[04 - Orquestrador Multi-Agente]]` |

## 🧠 Arquitetura Core para IAs
- **Topologia Antaris:** `[[Antaris-Architecture-For-AI]]` (Localizado em `00 - Sistema/Antaris-Architecture-For-AI.md`). Forneça este arquivo a qualquer sub-agente instanciado que vá atuar no código do orquestrador global.

## ⚙️ Protocolo de Operação RAG

1. **Classificação da Intenção:** Identificar a linguagem/plataforma requerida pelo usuário.
2. **Recuperação de Contexto:** Utilizar a habilidade `read_file` ou `obsidian` para ler o arquivo da Persona relevante em `00 - Sistema/01 - Personas/`.
3. **Injeção Silenciosa:** O agente deve injetar as regras e anti-padrões da Persona em seu próprio prompt de sistema para aquela sessão de trabalho.
4. **Execução:** Prover a resposta rigorosamente alinhada às regras da Persona lida.

> *Nota: Este índice será atualizado de forma autônoma à medida que novas demandas exigirem novas especializações.*