// Versions are pinned in settings.gradle.kts. The journal draws a web page now, so the only thing
// this build needs from a library is FileProvider, which core-ktx carries.
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Signing comes from the environment, so no key material is ever in this repository. CI writes
// the keystore out of the KEYSTORE_BASE64 secret and points SIGNING_STORE_FILE at it; a local
// build without those variables still assembles debug, and its release build is simply unsigned.
//
// The names are deliberately not storePassword/keyPassword/keyAlias: inside the
// signingConfigs block those are the DSL's own properties, and a local val of the same name would
// win the lookup on the right of the assignment.
val signingStorePath: String? = System.getenv("SIGNING_STORE_FILE")
val signingStorePass: String? = System.getenv("SIGNING_STORE_PASSWORD")
val signingKeyPass: String? = System.getenv("SIGNING_KEY_PASSWORD") ?: signingStorePass
val signingAlias: String = System.getenv("SIGNING_KEY_ALIAS") ?: "ujournal"

android {
    namespace = "app.ujournal"
    // Google Play rejects an upload that targets less than API 36: since 31 August 2026 an update
    // has to target Android 16, and AGP 8.10 is the oldest plugin that can compile against it.
    compileSdk = 36

    defaultConfig {
        applicationId = "app.ujournal"
        minSdk = 26
        targetSdk = 36
        // The version lives here, not in the run that built it. It used to be the workflow's run
        // number, which meant a build from a later run carried a higher versionCode than the
        // release cut before it - and Android refuses such a release as a downgrade. The code is
        // computed from the name and only ever goes up: 1.6.1 -> 10601.
        versionName = "1.6.1"
        versionCode = versionName!!.split(".").let { p ->
            p[0].toInt() * 10_000 + p[1].toInt() * 100 + p[2].toInt()
        }
        // Where the in-app updater looks for new releases (the repo must be public).
        buildConfigField("String", "GITHUB_REPO", "\"AnekTheGreat/Journal\"")
    }

    signingConfigs {
        // Only configured when the key is actually present, so a checkout with no secrets builds.
        if (signingStorePath != null && signingStorePass != null) {
            create("release") {
                storeFile = file(signingStorePath)
                storePassword = signingStorePass
                keyAlias = signingAlias
                keyPassword = signingKeyPass
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.findByName("release")
        }
    }

    buildFeatures {
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
}
