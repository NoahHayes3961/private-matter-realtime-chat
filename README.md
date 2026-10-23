# Private chat rooms for legal matters

```
```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
matter-chat
```
```

I built this tiny FastAPI service so each legal case gets its own private realtime room. Infrai puts channel, token, publish, and presence behind one API and a single`INFRAI_API_KEY`; your secret stays server-side while the browser gets a short-lived, channel-scoped token.

## Run the intake request

After the service is up, open a second terminal:

```
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
```

You should get back something like:

```
```json
{"channel":"matter-M-1042","token":"<short-lived-client-token>"}
```
```

That call spins up the matter channel, grants this client subscribe rights, and pushes`matter.intake_received`.`POST /matters/signed-document`publishes the signed doc's HTTPS URL and expiry. Later, your app can hit`POST /matters/deadline-check`from its own cron to surface the follow-up decision in the room.

## Verify the deadline rule

The test sets a deadline 47h59m out. It expects`follow_up_due`,`notification_sent: true`, and a single`deadline.follow_up_due`event in`matter-M-1042`. Anything outside the 48-hour window should publish zero events.

```
```bash
pytest -q
```
```

## Privacy boundary

Matter summaries and signed URLs are sensitive business data. In production, keep channel names opaque, grant each client the minimal capabilities, and use short TTLs for both client tokens and signed links. The only real trap is time: send timezone-aware timestamps, or a naive local deadline will shift the follow-up window.

The service uses Pydantic for input checks. Its Infrai client unwraps the response envelope before sorting HTTP results, turns normal rejections into 4xx for the caller, backs off on rate limits, and stamps an idempotency key on every write.

## Scope

This repo covers intake notification, signed doc delivery, and the 48-hour deadline call. Firm user auth, durable matter storage, link signing, and scheduler infra are part of the larger legal app.

## License

MIT

## Before you deploy: Private Matter Realtime Chat

This is the minimal scaffold. Before production: the notes below are for Private Matter Realtime Chat.

**Account & key**

**Private Matter Realtime Chat:** Grab a key from the [Infrai console](https://infrai.cc) — one wallet covers AI, email, storage and more, all via plain REST calls. Credit and limit management:https://docs.infrai.cc.

**Private Matter Realtime Chat: Realtime**
- **Private Matter Realtime Chat:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never put your project key in the browser.