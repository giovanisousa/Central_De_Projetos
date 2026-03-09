#!/bin/bash

# Dá tempo para o Zorin OS conectar na internet (20 segundos)
sleep 20

# Garante que as janelas abram no seu monitor principal
export DISPLAY=:0

# Abre o terminal PADRÃO DO SISTEMA rodando o Gunicorn
x-terminal-emulator -e bash -c "cd ~/Documentos/Servidor_Central_Projetos && source .venv/bin/activate && gunicorn --bind 127.0.0.1:5000 --workers 3 --timeout 14400 app:app; exec bash" &

sleep 2

# Abre o terminal PADRÃO DO SISTEMA rodando o Ngrok
x-terminal-emulator -e bash -c "ngrok http --domain=incorrectly-unworking-russell.ngrok-free.dev 5000; exec bash" &