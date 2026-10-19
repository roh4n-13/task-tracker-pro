package com.tasktracker.app;

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
                    resultJson = "{\"success\":false,\"error\":\"Empty server response\"}";
                    isSuccess = false;
                }
            } catch (Exception e) {
                resultJson = "{\"success\":false,\"error\":\"Network error: " + e.getMessage() + "\"}";
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
}\n