# Hydrotwin

Data: 16/04/2026 - v2

## Decisões de tech

Escolha de banco de dados: SQLite - arquivo local leve e simplficado

Escolha de dashboard: Streamlit - roda local e pode ser hospedado na web eventualmente

---

## Arquitetura

[Sensores]
     ↓
[Arduino Mega]
     ↓ (Serial USB)
[Raspberry Pi 4]
     ↓
[Script Python]
     ↓
[SQLite]
     ↓
[Streamlit Dashboard]

Comunicação Serial Pura --> csv ou vetor

Arduino faz pré processamento > coleta dados, agrega eles e envia a cada 10 segundos para o rasp

---

## Sensores

- ph
- ec
- luminosidade
- temp_agua
- temp_ambiente
- fluxo_agua
- nivel_tanque
- umidade

---

## Banco de Dados

### Tabelas do banco

Bancada: id, nome

Cultura: id, nome, ph min, ph max, ec min, ec max

Filete: id, bancada_id, cultura_id, dt_plantio, dt_prevs_colheita

Sensor_raw_data: id, bancada_id, coletado_em, luminosidade, temp_agua, temp_ambiente, fluxo_agua, umidade, nivel_tanque, ec, ph

Sensor_processado: id, bancada_id, janela, calculado_em, media_ph, media_ec, media_temp_agua, media_temp_ambiente, media_fluxo_agua, media_umidade, media_luminosidade, max_ph, max_ec, max_temp_agua, max_temp_ambiente, max_fluxo_agua, max_umidade, max_luminosidade, min_ph, media_ec, min_temp_agua, min_temp_ambiente, min_fluxo_agau, min_umidade, min_luminosidade, n_amostras

Alertas: id, bancada_id, sensor_raw_id, senor, severidade, mensagem, valor_medido, valor_lim_max, valor_lim_min, criado_em, resolvido_em

### Indíces

Sensor_raw_data: raw_bancada_tempo, raw_tempo

Sensor_processado: proc_bancada_janela_tempo, proc_tempo_janela

Alerta: alerta_bancada_criado, alerta_aberto

Filete: filete_bancada

---

## Lógicas Implementadas

### Classificação

Aqui a ideia foi classificar o estado da bancada em 3 possíveis status:

- Saudável
- Atenção
- Crítico

A clafissicação é triggada a cada 10 segundos e trigga os alertas.

Tem seu próprio arquivo de lógica, mas a interação com o banco está toda no crud.

### Alerta

É criado toda vez que o status é "Atenção" ou "Crítico".  Fica armazenado na tabela de alertas e é exibida para o usuário na Visão Geral.

Não tem seu próprio arquivo de lógica, está tudo no crud, sincronizado com o crud de Classifiicação.

### Anomalia

A ideia é de detectar anomalias estatísitcas nos dados coletados / fakeados.

A classificação de anomalias é similar a classificação de estado.

Tem seu prórpio arquivo de lógica, não possui tabela no banco que guarde essa métrica, é apenas exibido no Monitoramento Detalhado.

---

## Anoações

### Bugs de front end:

- nome da bancada não reseta após envio
- quero poder filtrar por bancada, por sensores, por periodo na aba monitoramento
- tudo referente a front pode ser melhorado

### A fazer:

- arrumar página inicial com descritivo do projeto, imagens, etc
- escrever um readme decente
- organizar o diretório

### Revisar:

- Lógica de risco
- Lógica de anomalia
- Lógica de tendência
