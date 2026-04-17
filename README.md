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

## Anoações

### Bugs de front end:

- nome da bancada não reseta após envio
- quero poder filtrar por bancada, por sensores, por periodo na aba monitoramento

### A fazer:

- separar lógica de classificação e outros calculos em outro arquivo
- arrumar página inicial com descritivo do projeto, imagens, etc
- escrever um readme decente
- organizar o diretório
