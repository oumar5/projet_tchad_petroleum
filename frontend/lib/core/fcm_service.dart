import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import 'api_client.dart';

/// Wraps Firebase Messaging — registration of the device token + send to backend.
class FcmService {
  FcmService(this._client);
  final ApiClient _client;

  Future<void> init() async {
    try {
      await Firebase.initializeApp();
    } catch (e) {
      debugPrint('FCM init skipped (no Firebase config): $e');
      return;
    }
    final m = FirebaseMessaging.instance;
    await m.requestPermission();
    final token = await m.getToken();
    if (token != null) {
      await _registerToken(token);
    }
    m.onTokenRefresh.listen(_registerToken);
  }

  Future<void> _registerToken(String token) async {
    try {
      await _client.dio.patch(
        '/v1/notifications/preferences',
        data: {'fcm_token': token},
      );
    } catch (_) {/* best effort */}
  }
}
