import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStorage {
  TokenStorage(this._storage);
  final FlutterSecureStorage _storage;

  static const _refreshKey = 'sb.refresh_token';

  Future<void> saveRefreshToken(String token) =>
      _storage.write(key: _refreshKey, value: token);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  Future<void> clear() => _storage.delete(key: _refreshKey);
}
