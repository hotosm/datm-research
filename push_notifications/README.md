# Push Notifications

iOS now also supports the Push API for web, so push notifications from a
PWA is now possible.

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
