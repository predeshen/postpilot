# PostPilot Android App

Native Android application built with Kotlin and Jetpack Compose. Provides a Material 3 interface for managing AI-generated social media content across TikTok, Instagram, and Facebook. Built for South African businesses.

## App Architecture

The app follows the **MVVM (Model-View-ViewModel)** pattern with **Jetpack Compose** for the UI layer:

```
app/src/main/java/com/marketingai/app/
├── MainActivity.kt              # Single activity, hosts Compose navigation
├── PostPilotApp.kt              # Application class (Hilt entry point)
├── data/
│   ├── api/
│   │   ├── ApiClient.kt         # Retrofit/OkHttp configuration
│   │   └── ApiService.kt        # Retrofit interface (all API endpoints)
│   ├── local/
│   │   └── AppDatabase.kt       # Room database for local caching
│   ├── models/
│   │   └── Models.kt            # Data classes (request/response models)
│   └── repository/
│       ├── AnalyticsRepository.kt
│       ├── BusinessRepository.kt
│       ├── ContentRepository.kt
│       ├── ScheduleRepository.kt
│       └── TrendsRepository.kt
├── di/
│   └── AppModule.kt             # Hilt dependency injection module
├── navigation/
│   └── NavGraph.kt              # Navigation routes and screen transitions
└── ui/
    ├── components/              # Reusable Compose components
    │   ├── BrandVoiceSelector.kt
    │   ├── CalendarView.kt
    │   ├── ColorPicker.kt
    │   ├── DaySelector.kt
    │   ├── HashtagChip.kt
    │   └── PlatformPostCard.kt
    └── screens/
        ├── analytics/           # Performance analytics
        ├── content/             # Content preview and editing
        ├── dashboard/           # Main dashboard
        ├── onboarding/          # Business setup wizard
        ├── schedule/            # Posting schedule management
        ├── settings/            # App settings
        └── trending/            # Trending hashtags explorer
```

### Layer Responsibilities

| Layer | Responsibility |
|-------|---------------|
| **UI (Screens + Components)** | Compose UI, user interaction, state observation |
| **ViewModel** | Holds UI state, handles user actions, calls repositories |
| **Repository** | Abstracts data sources, coordinates API and local DB |
| **API Service** | Retrofit interface defining all backend endpoints |
| **Local DB** | Room database for offline caching and drafts |
| **DI Module** | Hilt provides singletons for Retrofit, Room, repositories |

### Data Flow

```
User Action -> Screen -> ViewModel -> Repository -> ApiService -> Backend
                                                 -> Room DB (cache)
```

State flows back through `StateFlow` / `State<T>` in ViewModels, observed by Compose screens.

## Screen Descriptions

### Onboarding Screen
The first screen new users see. A step-by-step wizard to set up their business profile:
- Business name and industry selection
- Brand voice selection (professional, casual, bold, inspirational, playful, luxurious)
- Brand color picker
- Target audience definition
- Unique selling points entry

Once complete, the profile is sent to the backend via `POST /api/business/setup`.

### Dashboard Screen
The main hub after onboarding. Displays:
- Quick stats (total posts, published, scheduled)
- Recent generated content with platform cards
- Quick-action buttons to generate content, view schedule, or check trends
- Navigation to all other screens

### Content Preview Screen
Shows a generated post in full detail:
- Full post text with platform-specific formatting preview
- Hashtag chips (tappable)
- Generated image preview (if available)
- Theme consistency score indicator
- Actions: Approve, Reject, Regenerate, Edit
- Platform indicator (TikTok/Instagram/Facebook styling)

### Schedule Screen
Manage posting schedules:
- Weekly calendar view showing scheduled slots
- Day selector for viewing specific days
- Add/edit schedule slots with time picker
- Platform filter tabs
- Best posting time suggestions from the backend
- Content series assignments (Monday Motivation, Tip Tuesday, etc.)

### Trending Screen
Explore trending hashtags:
- Platform selector tabs (TikTok, Instagram, Facebook)
- Industry filter
- Hashtag cards with trend scores and relevance indicators
- Competitor analysis section showing their top hashtags and strategies
- Copy-to-clipboard for individual hashtags

### Analytics Screen
Performance tracking:
- Overall performance metrics cards
- Posts by platform breakdown
- Posts by status distribution
- Theme consistency score with breakdown
- Content pillar balance visualization
- Recommendations for improving content strategy

### Settings Screen
App configuration:
- Backend URL configuration
- Business profile editing (redirects to update flow)
- Language preferences
- Cache management
- About/version info

## Build Instructions

### Requirements

- **Android Studio Hedgehog (2023.1.1)** or newer
- **JDK 17** (bundled with Android Studio)
- **Android SDK 34** (compileSdk)
- **Min SDK 26** (Android 8.0+)
- Kotlin 1.9+
- Gradle 8.14

### Setup Steps

1. Open Android Studio
2. Select **File > Open** and navigate to the `android-app/` directory
3. Wait for Gradle sync to complete (downloads all dependencies)
4. Connect an emulator or physical device (API 26+)
5. Click **Run** (green play button) or use `Shift+F10`

### Build from Command Line

```bash
cd android-app/

# Debug build
./gradlew assembleDebug

# Release build (requires signing config)
./gradlew assembleRelease

# Run tests
./gradlew test

# Run lint checks
./gradlew lint
```

### Build Variants

| Variant | `BASE_URL` | Debugging |
|---------|-----------|-----------|
| `debug` | `http://10.0.2.2:8000` (emulator localhost) | Enabled |
| `release` | Same default (override for production) | Disabled, minified |

To change the backend URL, edit `app/build.gradle.kts`:

```kotlin
buildConfigField("String", "BASE_URL", "\"https://your-production-url.run.app\"")
```

## Connecting to the Backend

### Local Development (Emulator)

The app defaults to `http://10.0.2.2:8000` which Android emulators route to the host machine's `localhost:8000`. Steps:

1. Start the backend: `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Run the app on an Android emulator
3. The app connects automatically

### Local Development (Physical Device)

For a physical device on the same network:

1. Find your machine's local IP (e.g., `192.168.1.100`)
2. Update `BASE_URL` in `build.gradle.kts` to `http://192.168.1.100:8000`
3. Ensure your firewall allows port 8000
4. Rebuild and run

### Production (AWS Lambda)

1. Deploy the backend to AWS Lambda (see main README)
2. Update `BASE_URL` to your API Gateway URL (https://{api-id}.execute-api.{region}.amazonaws.com)
3. Build a release APK

### Network Security Config

For local HTTP development (non-HTTPS), the app includes a network security config that allows cleartext traffic to `10.0.2.2` and `localhost`. For production, always use HTTPS.

## Key Libraries

| Library | Version | Why |
|---------|---------|-----|
| **Jetpack Compose** | BOM-managed | Modern declarative UI - less boilerplate than XML layouts, better state management, faster iteration |
| **Material 3** | BOM-managed | Google's latest design system with dynamic color support and modern components |
| **Hilt** | Latest | Official Android DI solution - simpler than Dagger, lifecycle-aware, good Compose integration |
| **Retrofit + Moshi** | Latest | Industry standard HTTP client. Moshi is faster and safer than Gson for Kotlin (supports nullability) |
| **Room** | Latest | First-party SQLite abstraction with compile-time query verification and coroutine support |
| **Navigation Compose** | Latest | Type-safe navigation integrated with Compose lifecycle. Handles back stack and deep links |
| **Coil** | Latest | Kotlin-first image loading library. Lighter than Glide, built on coroutines, Compose integration |
| **DataStore** | Latest | Replacement for SharedPreferences. Type-safe, async, no ANR risk from disk I/O on main thread |
| **Coroutines** | Latest | Structured concurrency for async operations. All network and DB calls are suspend functions |
| **KSP** | Latest | Kotlin Symbol Processing for annotation processing (Hilt, Room, Moshi). Faster than kapt |

### Why These Choices

- **Compose over XML:** Less code, better preview tooling, easier state management, no need for view binding
- **Hilt over manual DI:** Compile-time validation, less boilerplate, integrates with ViewModel and Navigation
- **Moshi over Gson:** Kotlin-aware (handles `val`, nullability, default values), code generation (no reflection)
- **Room over raw SQLite:** Type-safe queries, compile-time verification, migration support, Flow/coroutine integration
- **Coil over Glide:** Native Kotlin, smaller binary, coroutine-based, first-class Compose support
- **Single Activity:** Standard modern Android architecture - one Activity hosts all Compose screens via Navigation
