import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.compile.JavaCompile
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask

plugins {
    id("com.android.application")
}

val cottProjectDirectory = rootProject.layout.projectDirectory.dir("..")
val cottDeploymentDirectory = layout.buildDirectory.dir("cott-runtime")
val cottExecutable = providers.environmentVariable("COTT_BIN").orElse("cott")
val cottProjectPath = cottProjectDirectory.asFile.absolutePath

val cottEmitKotlin = tasks.register<Exec>("cottEmitKotlin") {
    group = "cott"
    description = "Emits the Cott Kotlin module."
    workingDir(cottProjectDirectory)
    executable(cottExecutable.get())
    args("emit", "kotlin", "--project", cottProjectPath)
}

val cottVerify = tasks.register<Exec>("cottVerify") {
    group = "cott"
    description = "Verifies the emitted Cott Kotlin module."
    dependsOn(cottEmitKotlin)
    workingDir(cottProjectDirectory)
    executable(cottExecutable.get())
    args("verify", "--project", cottProjectPath)
}

val cottDeploy = tasks.register<Exec>("cottDeploy") {
    group = "cott"
    description = "Deploys the verified Cott module for this Android app."
    dependsOn(cottVerify)
    workingDir(cottProjectDirectory)
    executable(cottExecutable.get())
    args(
        "deploy",
        "--project",
        cottProjectPath,
        "--output",
        cottDeploymentDirectory.get().asFile.absolutePath,
    )
    outputs.dir(cottDeploymentDirectory)
    outputs.upToDateWhen { false }
    doFirst {
        project.delete(cottDeploymentDirectory)
    }
}

val cottRuntimeClasspath = files(
    cottDeploymentDirectory.map { it.file("cott-module.jar") },
    fileTree(cottDeploymentDirectory.map { it.dir("runtime-libs") }) {
        include("*.jar")
        exclude("kotlin-stdlib*.jar")
    },
).builtBy(cottDeploy)

android {
    namespace = "dev.cott.counter"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.cott.counter"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

dependencies {
    implementation(cottRuntimeClasspath)
}

tasks.named("preBuild") {
    dependsOn(cottDeploy)
}

tasks.withType<KotlinCompilationTask<*>>().configureEach {
    dependsOn(cottDeploy)
}

tasks.withType<JavaCompile>().configureEach {
    dependsOn(cottDeploy)
}
