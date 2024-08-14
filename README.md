# Elastic Streaming Use Case (Filebeat + Kafka + Logstash)

## Tabla de Contenidos

1. [Descripción](#descripción)
2. [Componentes de la Solución](#componentes-de-la-solución)
   - [Filebeat](#filebeat)
   - [Kafka](#kafka)
   - [Logstash](#logstash)
3. [Requisitos](#requisitos)
4. [Pasos para la Implementación](#pasos-para-la-implementación)
5. [Ejemplo de Configuración](#ejemplo-de-configuración)
   - [Filebeat (filebeat.yml)](#filebeat-filebeatyml)
   - [Kafka (docker-compose.yml)](#kafka-docker-composeyml)
   - [Logstash (logstash.conf)](#logstash-logstashconf)
6. [Pruebas y Validación](#pruebas-y-validación)
   - [Despliegue del servidor de Apache Kafka](#despliegue-del-servidor-de-apache-kafka)
   - [Crear el topic necesario](#crear-el-topic-necesario)
   - [Ejecución de Filebeat](#ejecución-de-filebeat)
   - [Ejecución de Logstash](#ejecución-de-logstash)
7. [Simulación de Escritura de Logs](#simulación-de-escritura-de-logs)

---
## Descripción

La empresa TODO1 cuenta con un sistema de información (Sistema X) que genera múltiples archivos de log en formato JSON. Esta información necesita ser enviada a otro sistema (Sistema Y) que no es compatible con archivos JSON. Se requiere una prueba de concepto para una solución de streaming en casi tiempo real que lea los archivos JSON del Sistema X y los convierta a un formato que el Sistema Y pueda procesar, como CSV u otro formato compatible.

## Componentes de la Solución

1. ### Filebeat: 
   - **Función**: Captura los archivos de log JSON generados por el Sistema X.
   - **Configuración**: Filebeat está configurado para leer los archivos de log desde el Sistema X y cambiar su formato de json a csv y enviarlos a Kafka para su procesamiento.

2. ### Kafka: 
   - **Función**: Actúa como el intermediario de mensajes que recibe los archivos de log JSON desde Filebeat.
   - **Configuración**: Configurado para recibir mensajes en formato JSON y transmitirlos a Logstash para la conversión.

3. ### Logstash: 
   - **Función**: Procesa los mensajes recibidos desde Kafka y los muestra en consola por la salida estandar.
   - **Configuración**: Configurado para consumir los mensajes de Kafka.

## Requisitos
- **Docker/docker-compose** para virtualización y despliegue de la solucion

## Pasos para la Implementación

1. **Configurar Filebeat**:
   - Establecer la configuración para leer archivos JSON.
   - Procesar los datos a un formato csv
   - Enviar los datos a kafka

3. **Configurar Logstash**:
   - Configurar los pipelines para consumir datos desde Kafka.

4. **Verificar la Solución**:
   - Realizar pruebas para asegurar que los datos se leen correctamente desde los archivos JSON y se convierten en el formato adecuado para el Sistema Y.

## Ejemplo de Configuración

### Filebeat (filebeat.yml)
```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - C:\Users\romar\OneDrive\Desktop\prueba-tecnica\TODO1\*.json
    # json.keys_under_root: true
    # json.add_error_key: true

processors:
  - decode_json_fields:
      fields: ["message"]
      target: ""
  - drop_fields:
      fields: ["@timestamp", "log", "input", "ecs", "host", "agent"]
  - script:
      lang: javascript
      id: convert_to_csv
      source: >
        function process(event) {
          var data = event.Get("message");
          if (data) {
            try {
              var json = JSON.parse(data);
              var keys = Object.keys(json);
              var values = keys.map(function(key) {
                return json[key];
              });
              var csv = keys.join(";") + "\n" + values.join(";");
              csv = csv.trim()
              event.Put("message", csv);
            } catch (e) {
              event.Put("message", "Error converting JSON to CSV: " + e.message);
            }
          }
        }

output.kafka:

  hosts: ["localhost:9092"]
  topic: "todo1-ej-topic"
  partition.round_robin:
    reachable_only: false
  required_acks: 1
  compression: gzip
  max_message_bytes: 1000000
  codec:
    format:
      string: "%{[message]}"

```

### Kafka (docker-compose.yml)
```yaml
services:
  kafka:
    build:
      context: .
      dockerfile: Dockerfile.kafka
    container_name: kafka
    ports:
      - 9092:9092
    environment:
      KF_SERVER: --bootstrap-server kafka:9092
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://kafka:9092,CONTROLLER://localhost:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1 # esto genera el  __consumer_offsets de lo contraio da
      # KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      # KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      # KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
  logstash:
    # image: docker.elastic.co/logstash/logstash:8.15.0
    build:
      context: .
      dockerfile: Dockerfile.logstash
    container_name: logstash
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      - ./logstash.yml:/usr/share/logstash/config/logstash.yml
    depends_on:
      - kafka
    ports:
      - "5044:5044"

    environment:
      ELASTIC_CONTAINER: false

  filebeat:
    # image: elastic/filebeat:8.15.0
    build:
      context: .
      dockerfile: Dockerfile.filebeat
    container_name: filebeat
    depends_on:
      - kafka
    volumes:
      - ./TODO1/:/usr/share/filebeat/TODO1/
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
```

### Logstash (logstash.conf)
```plaintext
input {
  kafka {
    bootstrap_servers => "localhost:9092"
    topics => ["todo1-ej-topic"]
  }
}


output {
  stdout {
    codec => rubydebug  
  }
}

```



## Pruebas y Validación
### 1. Despliegue 
  ```bash
   docker-compose up
   ```

### 2. Simulación de Escritura de Logs

  Para simular la generación de archivos de log JSON, se usa el siguiente script en Python. Este script crea un archivo `output.json` y escribe un nuevo registro JSON en él cada 5 segundos:

```python
import json
import time
import random
import os

def generate_json_data(age):
    return json.dumps({"age": age, "other": random.randint(0,9)})

target = "./TODO1/output.json"
if os.path.exists(target):
    os.remove(target)

age = 1
interval = 5
while True:
    json_data = generate_json_data(age)
    with open(target, "a") as file:
        file.write(json_data + "\n")
    print(json_data)
    age += 1
    time.sleep(interval)
```

Ejecutar

   ```bash
   python generate_logs.py
   ```