import os

files = {}

# 1. GITIGNORE
files[".gitignore"] = """
*.iml
.gradle
/local.properties
/.idea
.DS_Store
/build
/captures
"""

# 2. ROOT GRADLE
files["build.gradle"] = """
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.2.2'
    }
}
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
task clean(type: Delete) {
    delete rootProject.buildDir
}
"""

# 3. SETTINGS GRADLE
files["settings.gradle"] = """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "TaskTracker"
include ':app'
"""

# 4. GRADLE PROPERTIES
files["gradle.properties"] = """
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
"""

# 5. GITHUB ACTIONS APK BUILDER
files[".github/workflows/build-apk.yml"] = """
name: Build Android APK

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    name: Build Debug APK
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Set up Android SDK
        uses: android-actions/setup-android@v3

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3
        with:
          gradle-version: '8.5'

      - name: Build Debug APK
        run: gradle assembleDebug --no-daemon --stacktrace

      - name: Verify APK
        run: |
          APK_PATH=$(find app/build/outputs/apk/debug -name "*.apk" | head -n 1)
          if [ -z "$APK_PATH" ] || [ ! -s "$APK_PATH" ]; then
            echo "::error::Build did not produce a valid APK!"
            exit 1
          fi
          echo "APK successfully built at: $APK_PATH"
          ls -lh "$APK_PATH"

      - name: Upload Debug APK
        uses: actions/upload-artifact@v4
        with:
          name: task-tracker-debug-apk
          path: app/build/outputs/apk/debug/*.apk
          retention-days: 14
"""

# 6. APP BUILD GRADLE
files["app/build.gradle"] = """
plugins {
    id 'com.android.application'
}

android {
    namespace 'com.tasktracker.app'
    compileSdk 34

    defaultConfig {
        applicationId "com.tasktracker.app"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
        debug {
            applicationIdSuffix ".debug"
            debuggable true
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.core:core:1.12.0'
    implementation 'androidx.activity:activity:1.8.2'
}
"""

# 7. ANDROID MANIFEST
files["app/src/main/AndroidManifest.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.tasktracker.app">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.TaskTracker"
        android:usesCleartextTraffic="false"
        android:networkSecurityConfig="@xml/network_security_config">

        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:exported="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <receiver
            android:name=".TaskReminderReceiver"
            android:exported="false" />

        <receiver
            android:name=".BootReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
            </intent-filter>
        </receiver>

    </application>
</manifest>
"""

# 8. RESOURCES
files["app/src/main/res/values/strings.xml"] = """<resources>
    <string name="app_name">Task Tracker</string>
</resources>
"""

files["app/src/main/res/values/styles.xml"] = """<resources>
    <style name="Theme.TaskTracker" parent="Theme.AppCompat.Light.NoActionBar">
        <item name="colorPrimary">#1976d2</item>
        <item name="colorPrimaryDark">#115293</item>
        <item name="colorAccent">#1976d2</item>
        <item name="android:windowBackground">#f4f6f9</item>
    </style>
</resources>
"""

files["app/src/main/res/xml/network_security_config.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
</network-security-config>
"""

files["app/src/main/res/drawable/ic_notification.xml"] = """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M19,3H5C3.89,3 3,3.89 3,5v14c0,1.1 0.89,2 2,2h14c1.1,0 2,-0.9 2,-2V5C21,3.89 20.1,3 19,3zM10,17l-5,-5 1.41,-1.41L10,14.17l7.59,-7.59L19,8l-9,9z"/>
</vector>
"""

# 9. JAVA CODE: MAIN ACTIVITY
files["app/src/main/java/com/tasktracker/app/MainActivity.java"] = """package com.tasktracker.app;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private AndroidBridge bridge;

    private final ActivityResultLauncher<String> requestPermissionLauncher =
            registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
                if (webView != null) {
                    webView.post(() -> webView.evaluateJavascript("window.onNotificationPermissionResult(" + isGranted + ");", null));
                }
                if (isGranted) {
                    Toast.makeText(this, "Daily reminders enabled!", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(this, "Notifications disabled. Enable in Settings for daily reminders.", Toast.LENGTH_LONG).show();
                }
            });

    @Override
    @SuppressLint("SetJavaScriptEnabled")
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);

        bridge = new AndroidBridge(this, webView, this::requestNotificationPermission);
        webView.addJavascriptInterface(bridge, "AndroidBridge");

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (webView != null && webView.canGoBack()) {
                    webView.goBack();
                } else {
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
    }

    public void requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                requestPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS);
            } else {
                webView.post(() -> webView.evaluateJavascript("window.onNotificationPermissionResult(true);", null));
            }
        } else {
            webView.post(() -> webView.evaluateJavascript("window.onNotificationPermissionResult(true);", null));
        }
    }

    @Override
    protected void onDestroy() {
        if (bridge != null) bridge.cleanup();
        if (webView != null) webView.destroy();
        super.onDestroy();
    }
}
"""

# 10. JAVA CODE: ANDROID BRIDGE
files["app/src/main/java/com/tasktracker/app/AndroidBridge.java"] = """package com.tasktracker.app;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.Toast;

import androidx.core.app.NotificationManagerCompat;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.lang.ref.WeakReference;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Calendar;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AndroidBridge {

    private final Context context;
    private final WeakReference<WebView> webViewRef;
    private final Runnable permissionRequester;
    private final ExecutorService networkPool = Executors.newFixedThreadPool(4);

    public AndroidBridge(Context context, WebView webView, Runnable permissionRequester) {
        this.context = context.getApplicationContext();
        this.webViewRef = new WeakReference<>(webView);
        this.permissionRequester = permissionRequester;
    }

    @JavascriptInterface
    public void showToast(String message) {
        if (message != null) Toast.makeText(context, message, Toast.LENGTH_SHORT).show();
    }

    @JavascriptInterface
    public void copyToClipboard(String text) {
        ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard != null && text != null) {
            ClipData clip = ClipData.newPlainText("Task Report", text);
            clipboard.setPrimaryClip(clip);
            showToast("Copied to clipboard!");
        }
    }

    @JavascriptInterface
    public void shareText(String title, String text) {
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_SUBJECT, title != null ? title : "Task Report");
        intent.putExtra(Intent.EXTRA_TEXT, text != null ? text : "");
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Intent chooser = Intent.createChooser(intent, "Share Task Report");
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(chooser);
    }

    @JavascriptInterface
    public void requestNotificationPermission() {
        if (permissionRequester != null) {
            WebView webView = webViewRef.get();
            if (webView != null) webView.post(permissionRequester);
        }
    }

    @JavascriptInterface
    public boolean areNotificationsEnabled() {
        return NotificationManagerCompat.from(context).areNotificationsEnabled();
    }

    @JavascriptInterface
    public void scheduleDailyReminder(int hour, int minute) {
        SharedPreferences prefs = context.getSharedPreferences("task_tracker_prefs", Context.MODE_PRIVATE);
        prefs.edit().putBoolean("reminder_enabled", true).putInt("reminder_hour", hour).putInt("reminder_minute", minute).apply();

        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager == null) return;

        Intent intent = new Intent(context, TaskReminderReceiver.class);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context, 1001, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0)
        );

        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.HOUR_OF_DAY, hour);
        calendar.set(Calendar.MINUTE, minute);
        calendar.set(Calendar.SECOND, 0);

        if (calendar.getTimeInMillis() <= System.currentTimeMillis()) {
            calendar.add(Calendar.DAY_OF_YEAR, 1);
        }

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                if (alarmManager.canScheduleExactAlarms()) {
                    alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), pendingIntent);
                } else {
                    alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), pendingIntent);
                }
            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), pendingIntent);
            } else {
                alarmManager.setRepeating(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), AlarmManager.INTERVAL_DAY, pendingIntent);
            }
            showToast(String.format("Reminder set for %02d:%02d daily", hour, minute));
        } catch (SecurityException ex) {
            alarmManager.set(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), pendingIntent);
        }
    }

    @JavascriptInterface
    public void cancelDailyReminder() {
        SharedPreferences prefs = context.getSharedPreferences("task_tracker_prefs", Context.MODE_PRIVATE);
        prefs.edit().putBoolean("reminder_enabled", false).apply();

        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager != null) {
            Intent intent = new Intent(context, TaskReminderReceiver.class);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                    context, 1001, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0)
            );
            alarmManager.cancel(pendingIntent);
        }
        showToast("Daily reminders turned off");
    }

    @JavascriptInterface
    public void nativeHttp(String urlStr, String method, String payload, String callbackId) {
        networkPool.execute(() -> {
            String resultJson;
            boolean isSuccess;

            try {
                URL url = new URL(urlStr);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(25000);
                conn.setReadTimeout(25000);
                conn.setInstanceFollowRedirects(false);
                conn.setRequestMethod(method);

                if ("POST".equalsIgnoreCase(method) && payload != null) {
                    conn.setDoOutput(true);
                    conn.setRequestProperty("Content-Type", "text/plain;charset=utf-8");
                    byte[] bytes = payload.getBytes(StandardCharsets.UTF_8);
                    try (OutputStream os = conn.getOutputStream()) {
                        os.write(bytes);
                        os.flush();
                    }
                }

                int code = conn.getResponseCode();
                int redirectCount = 0;
                while ((code == HttpURLConnection.HTTP_MOVED_TEMP
                        || code == HttpURLConnection.HTTP_MOVED_PERM
                        || code == HttpURLConnection.HTTP_SEE_OTHER
                        || code == 307) && redirectCount < 5) {
                    redirectCount++;
                    String redirectUrl = conn.getHeaderField("Location");
                    conn.disconnect();
                    if (redirectUrl == null) break;

                    conn = (HttpURLConnection) new URL(redirectUrl).openConnection();
                    conn.setConnectTimeout(25000);
                    conn.setReadTimeout(25000);
                    conn.setRequestMethod("GET");
                    conn.setDoOutput(false);
                    code = conn.getResponseCode();
                }

                InputStream is = (code >= 200 && code < 400) ? conn.getInputStream() : conn.getErrorStream();
                StringBuilder sb = new StringBuilder();
                if (is != null) {
                    try (BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) sb.append(line);
                    }
                }
                resultJson = sb.toString();
                isSuccess = (code >= 200 && code < 300);

                if (resultJson.trim().isEmpty()) {
                    resultJson = "{\\\"success\\\":false,\\\"error\\\":\\\"Empty server response\\\"}";
                    isSuccess = false;
                }
            } catch (Exception e) {
                resultJson = "{\\\"success\\\":false,\\\"error\\\":\\\"Network error: " + e.getMessage() + "\\\"}";
                isSuccess = false;
            }

            String base64Response = Base64.encodeToString(resultJson.getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP);
            boolean finalSuccess = isSuccess;

            WebView webView = webViewRef.get();
            if (webView != null) {
                webView.post(() -> {
                    String script = String.format("window.onNativeHttpResponse('%s', %b, '%s');",
                            callbackId, finalSuccess, base64Response);
                    webView.evaluateJavascript(script, null);
                });
            }
        });
    }

    public void cleanup() {
        networkPool.shutdown();
    }
}
"""

# 11. JAVA CODE: RECEIVERS
files["app/src/main/java/com/tasktracker/app/TaskReminderReceiver.java"] = """package com.tasktracker.app;

import android.app.AlarmManager;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

import androidx.core.app.NotificationCompat;

import java.util.Calendar;

public class TaskReminderReceiver extends BroadcastReceiver {

    public static final String CHANNEL_ID = "task_reminders_channel";
    public static final int NOTIFICATION_ID = 2001;

    @Override
    public void onReceive(Context context, Intent intent) {
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Daily Task Reminders", NotificationManager.IMPORTANCE_DEFAULT
            );
            channel.setDescription("Daily review reminder for pending tasks.");
            manager.createNotificationChannel(channel);
        }

        Intent appIntent = new Intent(context, MainActivity.class);
        appIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                context, 0, appIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0)
        );

        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle("📋 Task Tracker Check-in")
                .setContentText("You have pending tasks scheduled. Tap to review your dashboard!")
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .setContentIntent(pendingIntent)
                .setAutoCancel(true);

        manager.notify(NOTIFICATION_ID, builder.build());
    }
}
"""

files["app/src/main/java/com/tasktracker/app/BootReceiver.java"] = """package com.tasktracker.app;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

import java.util.Calendar;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction()) ||
            Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction())) {

            SharedPreferences prefs = context.getSharedPreferences("task_tracker_prefs", Context.MODE_PRIVATE);
            if (!prefs.getBoolean("reminder_enabled", false)) return;

            int hour = prefs.getInt("reminder_hour", 9);
            int minute = prefs.getInt("reminder_minute", 0);

            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            if (alarmManager == null) return;

            Intent reminderIntent = new Intent(context, TaskReminderReceiver.class);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                    context, 1001, reminderIntent,
                    PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0)
            );

            Calendar calendar = Calendar.getInstance();
            calendar.set(Calendar.HOUR_OF_DAY, hour);
            calendar.set(Calendar.MINUTE, minute);
            calendar.set(Calendar.SECOND, 0);

            if (calendar.getTimeInMillis() <= System.currentTimeMillis()) {
                calendar.add(Calendar.DAY_OF_YEAR, 1);
            }

            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    if (alarmManager.canScheduleExactAlarms()) {
                        alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), pendingIntent);
                    } else {
                        alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), pendingIntent);
                    }
                } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, calendar.getTimeInMillis(), pendingIntent);
                }
            } catch (SecurityException ignored) {}
        }
    }
}
"""

# Write all files to disk
for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\\n")

print("SUCCESS: 100% of Android files generated!")