import 'package:dio/dio.dart';

import 'config.dart';
import 'token_storage.dart';

/// Holds the in-memory access token + builds a [Dio] with auto-refresh.
class ApiClient {
  ApiClient(this._storage) {
    dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      sendTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      contentType: 'application/json',
    ));
    dio.interceptors.add(_AuthInterceptor(this));
  }

  late final Dio dio;
  final TokenStorage _storage;
  String? _accessToken;

  void setAccessToken(String token) => _accessToken = token;
  void clearAccessToken() => _accessToken = null;
  String? get accessToken => _accessToken;
  TokenStorage get storage => _storage;
}

class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._client);
  final ApiClient _client;
  bool _refreshing = false;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = _client.accessToken;
    if (token != null && !options.path.contains('/v1/auth/login')) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    super.onRequest(options, handler);
  }

  @override
  Future<void> onError(
      DioException err, ErrorInterceptorHandler handler) async {
    final response = err.response;
    final isRetry = err.requestOptions.extra['_retried'] == true;
    if (response?.statusCode != 401 || isRetry || _refreshing) {
      return super.onError(err, handler);
    }
    final refresh = await _client.storage.readRefreshToken();
    if (refresh == null) return super.onError(err, handler);

    _refreshing = true;
    try {
      final r = await _client.dio.post(
        '/v1/auth/refresh',
        data: {'refresh_token': refresh},
        options: Options(headers: {'Authorization': null}),
      );
      final newAccess = r.data['access_token'] as String;
      _client.setAccessToken(newAccess);

      final req = err.requestOptions
        ..headers['Authorization'] = 'Bearer $newAccess'
        ..extra['_retried'] = true;
      final retried = await _client.dio.fetch(req);
      return handler.resolve(retried);
    } catch (_) {
      await _client.storage.clear();
      _client.clearAccessToken();
      return super.onError(err, handler);
    } finally {
      _refreshing = false;
    }
  }
}
