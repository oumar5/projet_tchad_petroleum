import 'package:dio/dio.dart';

import '../../../core/api_client.dart';

class AuthRepository {
  AuthRepository(this._client);
  final ApiClient _client;

  Future<({String access, String refresh})> login(
      {required String email, required String password, String? mfaCode}) async {
    final r = await _client.dio.post('/v1/auth/login', data: {
      'email': email,
      'password': password,
      'mfa_code': ?mfaCode,
    });
    final access = r.data['access_token'] as String;
    final refresh = r.data['refresh_token'] as String;
    _client.setAccessToken(access);
    await _client.storage.saveRefreshToken(refresh);
    return (access: access, refresh: refresh);
  }

  Future<Map<String, dynamic>> me() async {
    final r = await _client.dio.get('/v1/auth/me');
    return Map<String, dynamic>.from(r.data as Map);
  }

  Future<void> logout() async {
    final refresh = await _client.storage.readRefreshToken();
    if (refresh != null) {
      try {
        await _client.dio
            .post('/v1/auth/logout', data: {'refresh_token': refresh});
      } on DioException {
        /* ignore */
      }
    }
    await _client.storage.clear();
    _client.clearAccessToken();
  }
}
