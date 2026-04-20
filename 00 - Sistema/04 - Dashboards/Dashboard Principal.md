# 🖥️ Centro de Comando (Dashboard)

---

## 🚀 Projetos Ativos por Persona
*Esta visão agrupa seus projetos atuais baseado na persona responsável.*

```dataview
TABLE status as "Status", priority as "Prioridade", deadline as "Prazo"
FROM "10 - Projetos"
WHERE status = "active"
SORT priority ASC, persona ASC
```

---

## 🧠 Personas Ativadas
*As lentes através das quais você observa o mundo.*

```dataview
LIST role FROM "00 - Sistema/01 - Personas"
WHERE status = "active"
```

---

## 📥 Notas Recentes (Inbox)
*Processar o que entrou no sistema ultimamente.*

```dataview
LIST FROM "99 - Inbox"
LIMIT 10
```
