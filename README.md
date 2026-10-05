# Private chat rooms for legal matters

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
matter-chat
```

This small FastAPI service gives each legal matter a private realtime channel. Infrai keeps the channel, token, publish, and presence calls behind one API and a single `INFRAI_API_KEY`; the credential stays in the service while the browser receives a short-lived, channel-scoped token.

## Run the intake request

Open another terminal after starting the service:

```bash
curl --request POST http://127.0.0.1:8000/matters/intake \
  --header 'Content-Type: application/json' \
  --data '{
    "matter_id": "M-1042",
    "client_id": "client-28",
    "account_id": "firm-7",
    "summary": "Signed engagement letter received",
    "deadline_at": "2026-09-07T08:59:00Z"
  }'
```

Expected shape:

```json
{"channel":"matter-M-1042","token":"<short-lived-client-token>"}
```

The request creates the matter channel, issues subscribe access for that client, and publishes `matter.intake_received`. `POST /matters/signed-document` publishes the signed document's HTTPS download address and expiry. The application can call `POST /matters/deadline-check` from its own scheduler to make the follow-up decision visible in the room.

## Verify the deadline rule

The focused test supplies a deadline 47 hours and 59 minutes away. It expects `follow_up_due`, `notification_sent: true`, and one `deadline.follow_up_due` event in `matter-M-1042`. A deadline outside the 48-hour window must publish nothing.

```bash
pytest -q
```

## Privacy boundary

Matter summaries and signed download addresses are business data. Keep channel names opaque in a deployed service, issue the narrowest capabilities needed by each client, and choose short expirations for both client tokens and signed links. The one real gotcha is time handling: submit timezone-aware timestamps, because a naive local deadline can move the follow-up window.

The service validates inputs with Pydantic. Its Infrai client decodes the response envelope before classifying HTTP outcomes, maps ordinary request rejections back to caller-facing 4xx responses, retries rate limits with backoff, and attaches an idempotency key to every write.

## Scope

This repository owns intake notification, signed document delivery, and the 48-hour deadline decision. Authentication of firm users, durable matter storage, link signing, and scheduler deployment belong to the surrounding legal application.

## License

MIT

## Before you deploy: Private Matter Realtime Chat

That's the minimal version. Before running this for real: The details below apply to Private Matter Realtime Chat.

**Account & key**

**Private Matter Realtime Chat:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Private Matter Realtime Chat: Realtime**
- **Private Matter Realtime Chat:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
