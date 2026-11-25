# Plant Disease Expo app

## Run the app

Copy `.env.example` to `.env.local` and set at least:

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_APP_SCHEME=plant-disease
EXPO_PUBLIC_MOCK=1
```

Start:

```bash
npm install
npm run web
npm run android
npm run ios
```

Mock mode starts the UI without the backend or real models:

```bash
EXPO_PUBLIC_MOCK=1 npm run web
```

Native Google and Facebook sign-in require an Expo development build, not Expo Go.

## Quality

```bash
npm run typecheck
npm run lint
npm test -- --runInBand
npm run generate:api
```

Use HTTPS `EXPO_PUBLIC_API_URL` values for production builds.
