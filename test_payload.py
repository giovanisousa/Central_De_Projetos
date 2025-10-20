from datetime import date
import json

# Simular o que _resolver_custom_fields faz
custom_fields = {'data_de_homologacao': 'CURRENT_DATE'}
resolved = {}
for chave, valor in custom_fields.items():
    if isinstance(valor, str) and valor.upper() == 'CURRENT_DATE':
        resolved[chave] = date.today().strftime('%Y-%m-%d')
    else:
        resolved[chave] = valor

# Simular o payload que está sendo enviado no PATCH
payload = {
    'custom_fields': resolved
}

print('=== Payload que está sendo enviado atualmente ===')
print(json.dumps(payload, indent=2))
print('\n')

# Testar formato alternativo (sem custom_fields wrapper)
payload_alternativo = resolved

print('=== Payload alternativo (campos diretos) ===')
print(json.dumps(payload_alternativo, indent=2))
