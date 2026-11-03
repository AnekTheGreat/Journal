plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "app.ujournal"
    compileSdk = 34

    defaultConfig {
        applicationId = "app.ujournal"
        minSdk = 26
        targetSdk = 34
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = System.getenv("VERSION_NAME") ?: "1.0.0"
        // Where the in-app updater looks for new releases (the repo must be public).
        buildConfigField("String", "GITHUB_REPO", "\"AnekTheGreat/Journal\"")
    }

    signingConfigs {
        create("release") {
            storeFile = rootProject.file("ujournal.jks")
            storePassword = System.getenv("SIGNING_STORE_PASSWORD") ?: "ujournal123"
            keyAlias = System.getenv("SIGNING_KEY_ALIAS") ?: "ujournal"
            keyPassword = System.getenv("SIGNING_KEY_PASSWORD") ?: "ujournal123"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
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
