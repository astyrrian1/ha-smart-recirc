# Mechanical dashboard: Recirculation

The native Home Assistant view in [recirculation.json](../dashboards/recirculation.json) is installed as **Mechanical → Recirculation**, at `/dashboard-mechanical/recirculation`. The existing Mechanical Home recirculation section has a live pump tile and a link to this view; its existing history cards are preserved.

The view contains pump/schedule status, Start circulation and Stop pump actions, fault indicators, last received update, low/high temperatures, temperature difference, estimated flow rate and raw flow pulses, pump power/history, controller settings and explicit refresh. Stop is hidden while a controller schedule is active; the integration also enforces that guard. Start/stop use the existing integration buttons, not a power-cutting relay. The temperature labels preserve the verified low/high meanings and do not assume physical supply/return probe locations.

All cards are built into HA; no custom frontend resource or helper is needed. Existing entity IDs are used, including the historical raw-probe IDs. Version 0.4.0 adds the flow-rate entity; choose the installed meter in the integration options before its GPM value appears. The integration supplies persistent push updates; the timestamp means the latest received known field, not proof that every field changed then. The raw flow count is not cumulative volume. Operating settings retain the integration's validation.

## Deployment and rollback

Mechanical is a storage-mode dashboard, managed through HA's `lovelace/config` and `lovelace/config/save` WebSocket API. Before saving, export the full current config privately, compare it with a fresh read, and abort if another edit occurred. Append or replace only the view with path `recirculation`, preserving other views and cards. Validate every referenced entity against HA state, then read the saved config back and compare it with the proposed config. Do not edit `.storage` directly.

To install elsewhere, substitute the local entity IDs in this single-view JSON and add it to the desired dashboard's `views` array. The pump-power sensor is an existing separate power-monitor entity in this house; substitute or omit that tile and graph if absent. Roll back through the dashboard API using the saved prior config only after checking for subsequent user edits, or remove just the added view and overview cards through the UI.

## Verification — 2026-09-26

All 23 referenced entities existed in live HA. A private full-dashboard backup was saved before the API update, and a fresh-read comparison guarded against concurrent edits. Readback exactly matched the proposed configuration: two views (Home and Recirculation), all existing Home cards preserved, and the dedicated view identical to the checked-in JSON. No device actions were invoked during dashboard verification.

The browser session requires HA login, so visual rendering could not be verified. Native card types and action syntax follow the official [dashboard actions](https://www.home-assistant.io/dashboards/actions/), [tile](https://www.home-assistant.io/dashboards/tile/) and [conditional-card](https://www.home-assistant.io/dashboards/conditional/) documentation.
