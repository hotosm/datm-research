# Push Notifications

As of Q2 2023, iOS now also supports the Push API for web, so push notifications
from a PWA are now possible (in Chrome, Safari, Firefox).

For a basic demo of what push notifications look like, see
[here](https://whatpwacando.today/notifications)

- However this example is not the complete picture.
- To trigger the notification we need communication from a server --> mobile PWA.
- This happens by setting a listener on the PWA for notifications.
- We create a public/private key pair for secure communication between a server/user.
- Then the server can send a push notification to the users phone / PWA.

[Push API Docs](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
[Notifications API Docs](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)
[Usage example](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Tutorials/js13kGames/Re-engageable_Notifications_Push)

## Python Server Implementation

For Python the library we want to use is [pywebpush](https://github.com/web-push-libs/pywebpush)
This handles a lot of the stuff we would need to
[code ourselves](https://blog.mozilla.org/services/2016/08/23/sending-vapid-identified-webpush-notifications-via-mozillas-push-service)

This is an excellent guide:
https://pqvst.com/2023/11/21/web-push-notifications/
However it uses a Node backend.

Examples using Python backend:
https://jamesku.cc/blog/push-api-tutorial
https://tech.raturi.in/webpush-notification-using-python-and-flask

## How the browser Push API works under the hood

- You may be thinking, how on earth can the web browser receive a notification?
- Each web browser (chrome, firefox, safari) has it's own notification service.
- E.g. Mozilla's for Firefox: https://github.com/mozilla-services/autopush-rs
- When you create a VAPID key and register it, you are given a token for the
  web browsers push API.
- The web browser connects to this push API to receive the notification you send
  and displays it to the user.
- It's not magical - frontend's can't receive data - the actual server receiving data
  is provided by the browser vendor and tightly coupled to their browser.

## A note on 'native' notifications

- When developing a native (e.g. flutter) application, notifications need to be
  received by your phone somehow.
- Every Android or iOS device has a small service running in the background to     
  receive notifications.
- So users are vendor-locked to use tools like Firebase (Android) if they wish to
  send notifications to this service.
- It is technically possible to create your own notification listener service
  on a device, but not recommended (these official versions are heavily optimised
  for battery etc).
- The only good alternative to this is to use the web Push API as described above,
  where the equivalent to the mobile background service is the browser service 
  worker.

**tl;dr for a fully open-source approach to mobile notifications, the best option
as of 2024 is probably a PWA with the Push API.**

### Third-party notification listeners

- As described above, writing your own notification listener for mobile is not
  recommended.
- For completeness, there is one more approach, using a third-party server/app combo.
- Services like https://github.com/gotify/server can be self-hosted, providing a
  WebSocket-based approach that is used in combination with a mobile app to receive
  push notifications on your device.
- An alternative would be https://github.com/binwiederhier/ntfy, that uses a
  push/pull approach, again requiring a self-hosted server and an app installed.
- The downside of these approaches is they require an app to be installed on the
  users device to receive notifications, which isn't ideal.
