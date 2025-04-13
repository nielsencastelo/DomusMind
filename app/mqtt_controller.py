# publicação no MQTT
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883)

def enviar_acao(topico, comando):
    print(f"[MQTT] Enviando para {topico}: {comando}")
    client.publish(topico, comando)
