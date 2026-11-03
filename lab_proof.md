# Lab Proof — n8n Node Study Guide

## 1. Workflows analizados
- Workflow 1: PDF RAG con Cohere reranking.
- Workflow 2: respuesta comercial con rutas según company_size.
- Workflow 3: RAG con validación de consulta.

Tabla de nodos: [node_analysis.md](node_analysis.md)
Configuraciones exportadas: [workflow](workflow/)

## 2. Objetivo de mi Workflow 3
Es evitar consultas vacías al modelo y a Pinecone.
## 3. Entrada, regla y salida
- Entrada válida: `How long does setup take?`
- Entrada no válida: tres espacios.
- Regla: If comprueba si `chatInput` contiene texto después de aplicar `trim()`.
- Salida válida: el agente respondió que la configuración normal tarda entre 6 y 8 semanas, y entre 10 y 12 semanas para proyectos con más de tres almacenes. Citó LagerFlow Product FAQ.
- Salida no válida: `Escribe una pregunta sobre el documento.`

## 4. Evidencia de ejecución
- Rama True: [captura](evidence/workflow3_true.png)
- Rama False: [captura](evidence/workflow3_false.png)

En la prueba válida se ejecutaron Chat Trigger, If, RAG Agent, OpenAI Chat Model, Retrieve from Pinecone y Query Embeddings. If dirigió un item por True y el agente consultó Pinecone antes de responder.

En la prueba con espacios se ejecutaron Chat Trigger, If y Consulta vacía. If dirigió un item por False. El chat mostró el aviso y no se ejecutaron el agente, el modelo ni Pinecone.

## 5. Justificación del mapeo
Uso `chatInput` porque contiene la pregunta recibida del chat. La expresión `{{ ($json.chatInput ?? '').trim() }}` permite comprobar si está vacía, contiene solo espacios o no está presente. Esta comprobación no modifica el texto original.

Uso el campo `output` para entregar el aviso al chat, como comprobé en la prueba False. Consulta vacía conserva únicamente ese campo porque Include Other Input Fields está desactivado.

## 6. Primer fallo que monitorizaría
Monitorizaría la recuperación de fragmentos duplicados. En Workflow 1 observé tres resultados con el mismo contenido, IDs diferentes y la misma puntuación de relevancia. Esto reduce la variedad del contexto que recibe el modelo.

Para detectarlo, compararía el `pageContent` de los documentos recuperados y registraría cuántos contenidos distintos hay. La causa de los duplicados todavía no está confirmada. La validación de consultas vacías del Workflow 3 no resuelve este problema.

Como límite de la validación: tener texto no garantiza que la consulta sea clara o esté relacionada con el documento