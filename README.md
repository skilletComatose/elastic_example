# Elastic Streaming Use Case (Filebeat + Kafka + Logstash)

## Tabla de Contenidos

1. [Descripción](#descripción)
2. [Componentes de la Solución](#componentes-de-la-solución)
   - [Filebeat](#filebeat)
   - [Kafka](#kafka)
   - [Logstash](#logstash)
3. [Requisitos](#requisitos)
4. [Pasos para la Implementación](#pasos-para-la-implementación)
   - [Configurar Filebeat](#configurar-filebeat)
   - [Configurar Kafka](#configurar-kafka)
   - [Configurar Logstash](#configurar-logstash)
   - [Verificar la Solución](#verificar-la-solución)
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
- **Docker/docker-compose** para hacer el despliegue de kafka 
- **Filebeat** instalado en el Sistema X (para este caso tu maquina local).
- **Kafka** configurado con docker.
- **Logstash** configurado para recibir mensajes desde Kafka 

## Pasos para la Implementación

1. **Configurar Filebeat**:
   - Establecer la configuración para leer archivos JSON.
   - Procesar los datos a un formato csv
   - Enviar los datos a kafka

2. **Configurar Kafka**:
   - Configurar brokers y temas para recibir mensajes desde Filebeat.
   - Para este ejemplo el topic es : `todo1-topic`

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
  topic: "todo1-topic"
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
version: '3.8'
services:
  kafka-broker-1:
    build:
        context: .
        dockerfile: Dockerfile.kafka
    container_name: kafka 
    ports:
      - 9092:9092
    environment:
      KF_SERVER: --bootstrap-server localhost:9092

```

### Logstash (logstash.conf)
```plaintext
input {
  kafka {
    bootstrap_servers => "localhost:9092"
    topics => ["todo1-topic"]
  }
}


output {
  stdout {
    codec => rubydebug  
  }
}

```



## Pruebas y Validación
### 1. Despliegue del servidor de apacke kafka 
  ```bash
   docker-compose up
   ```
### 1.1 Configuracion del topic 
Crear el topic necesario para la prueba de concepto
  ```bash
   kafka-topics.sh $KF_SERVER --create --topic todo1-topic
   ```
  > nota:  $KF_SERVER solo es una variable de entorno que contiene el valor :  
   `--bootstrap-server localhost:9092`

### 2. Ejecucución de Filebeat
  ```bash
   filebeat -e
   ```
### 3. Ejecución de logstash
Ingresar a la ruta dode se encuentre instalado  y ejecutar
```bash
   bin/logstash -f <path de nuestro archivo>/logstash.conf
   ```
### 4. Simulación de Escritura de Logs

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