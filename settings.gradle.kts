pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    plugins {
        // API 36 needs AGP 8.10 or newer; Play has required API 36 for uploads since 31 Aug 2026.
        // The Compose plugin is not here any more: the screen is assets/index.html, so there is no
        // Compose in the build and no Compose compiler to pin.
        id("com.android.application") version "8.10.1"
        id("org.jetbrains.kotlin.android") version "2.0.21"
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "UJournal"
include(":app")
