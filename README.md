# GoHighLevel API Gateway (sofort testbar)

Kleiner Python-Service, der eingehende JSON-Daten an GoHighLevel (LeadConnector) weiterleitet.

## Starten

```bash
python3 gateway.py
```

Server läuft dann auf `http://localhost:8080`.

## Sofort testen (ohne echten API-Key)

```bash
export GHL_LOCATION_ID=deine_location_id
python3 gateway.py
```

In einem zweiten Terminal:

```bash
curl -sS -X POST http://localhost:8080/api/ghl/contact \
  -H 'Content-Type: application/json' \
  -d '{
    "firstName": "Max",
    "lastName": "Mustermann",
    "email": "max@example.com",
    "phone": "+491701234567",
    "tags": ["webform"],
    "customFields": []
  }' | jq
```

Wenn `GHL_API_KEY` **nicht** gesetzt ist, kommt eine `dry-run` Antwort zurück (perfekt zum direkten Testen).

## Live senden an GoHighLevel

```bash
export GHL_LOCATION_ID=deine_location_id
export GHL_API_KEY=dein_api_key
python3 gateway.py
```

Danach derselbe `curl`-Request wie oben. Dann wird wirklich an:

- `https://services.leadconnectorhq.com/contacts/`

gesendet.
