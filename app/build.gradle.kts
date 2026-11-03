plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
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
    compileSdk = 34

    defaultConfig {
        applicationId = "app.ujournal"
        minSdk = 26
        targetSdk = 34
        // The version lives here, not in the run that built it. It used to be the workflow's run
        // number, which meant a build from a later run carried a higher versionCode than the
        // release cut before it - and Android refuses such a release as a downgrade. The code is
        // computed from the name and only ever goes up: 1.2.2 -> 10202.
        versionName = "1.2.2"
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
        compose = true
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
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation(platform("androidx.compose:compose-bom:2024.09.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("io.coil-kt:coil-compose:2.7.0")
    implementation("io.coil-kt:coil-video:2.7.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
