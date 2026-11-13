// app/build.gradle.kts
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    id("com.chaquo.python") // Chaquopy: Android 本地嵌入式 Python 引擎
}

android {
    namespace = "com.example.geometrysolver"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.geometrysolver"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // 配置支持的 CPU 架构 (通常包含 arm64-v8a 和 armeabi-v7a)
        ndk {
            abiFilters.addAll(listOf("arm64-v8a", "armeabi-v7a", "x86_64"))
        }

        // Chaquopy 本地依赖配置: 离线安装 SymPy 用于数学符号求解
        chaquopy {
            defaultConfig {
                version = "3.10"
                pip {
                    install("sympy")
                }
            }
        }
    }

    buildFeatures {
        compose = true
    }
}

dependencies {
    // Jetpack Compose UI
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)

    // CameraX 相机拍摄
    implementation("androidx.camera:camera-core:1.4.0")
    implementation("androidx.camera:camera-camera2:1.4.0")
    implementation("androidx.camera:camera-lifecycle:1.4.0")
    implementation("androidx.camera:camera-view:1.4.0")

    // ONNX Runtime Mobile: 纯本地离线深度学习推理
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.19.2")

    // Coroutines 协程异步计算
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
