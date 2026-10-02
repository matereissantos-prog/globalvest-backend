plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }

android { namespace = "com.globalvest.app"; compileSdk = 35
    defaultConfig { applicationId = "com.globalvest.app"; minSdk = 26; targetSdk = 35; versionCode = 35; versionName = "3.5.0"
        buildConfigField("String", "API_BASE_URL", "\"https://globalvest-backend-1.onrender.com\"")
    }
    buildTypes { release { isMinifyEnabled = false; proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro") } }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    implementation("androidx.biometric:biometric:1.1.0")
}
