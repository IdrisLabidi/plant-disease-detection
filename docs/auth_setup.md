# Authentication provider setup

The setup below is the server-side contract for Google and Facebook login. The mobile/web app obtains
provider tokens and sends those tokens to the backend. The backend verifies them before creating or
linking an account.

## Google OAuth

Official references:
- Google identity: https://developers.google.com/identity
- Google ID token verification: https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.id_token.html

Create separate OAuth 2.0 client IDs for web, Android, and iOS where the provider console requires them.
Set every configured client ID in `GOOGLE_CLIENT_IDS`, separated by commas. The backend verifies the
ID token signature and claims, including expiry, issuer, audience, subject, and optional nonce.

Platform-specific redirect/package/bundle settings must be configured in the Google provider console:

- Web: configure an authorized JavaScript origin and redirect URI for the Expo web deployment.
- Android: configure the Android package name and SHA-1/SHA-256 certificate fingerprints.
- iOS: configure the iOS bundle identifier.

Final Android/iOS package and bundle values are application configuration details and could not be
verified from this repository, so mark them for the Expo app maintainer to fill in.

## Meta / Facebook Login

Official references:
- Graph `/debug_token`: https://developers.facebook.com/docs/graph-api/reference/v22.0/debug_token/
- Graph User: https://developers.facebook.com/docs/graph-api/reference/user/
- App and user access tokens: https://developers.facebook.com/docs/facebook-login/guides/access-tokens/

Create a Meta app and enable Facebook Login for each Expo platform used. Configure the app ID and app
secret:

- `FACEBOOK_APP_ID` - Meta application ID.
- `FACEBOOK_APP_SECRET` - Meta application secret.
- `FACEBOOK_GRAPH_VERSION` - Graph API version, for example `v22.0`.

The backend uses the app access token to inspect the user token with `/debug_token`, then fetches
`id`, `name`, and `email` from `/me`. Facebook email may be absent or not considered a trusted
verified email for account linking.

Configure valid OAuth redirect URIs and native platform package/bundle settings in the Meta app.
The exact Expo redirect URIs and bundle/package identifiers could not be verified from this repository.

Meta/privacy requirements:
- Add a publicly accessible privacy policy URL to the Meta app settings.
- Review the Meta data deletion requirements and configure a data deletion callback URL if the app
  processes Facebook Login data.
- The exact deletion callback route and callback-host URL are not verified and must be supplied by the
  deployment maintainer.
