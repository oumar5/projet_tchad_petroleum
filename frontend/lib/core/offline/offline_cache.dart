import 'dart:convert';

import 'package:hive_flutter/hive_flutter.dart';

/// Result of a cached fetch — exposes whether the value comes from cache and when it was fetched.
class CachedResult<T> {
  const CachedResult({
    required this.data,
    required this.fromCache,
    required this.fetchedAt,
    this.staleSinceFresh,
  });

  final T data;
  final bool fromCache;
  final DateTime fetchedAt;

  /// `true` if the cached entry is older than the freshness window.
  /// Always `false` when [fromCache] is `false`.
  final bool? staleSinceFresh;
}

/// Lightweight Hive-backed cache with TTL semantics + offline fallback helper.
class OfflineCache {
  OfflineCache._();
  static final OfflineCache instance = OfflineCache._();

  static const _box = 'sb.cache';
  static const _schemaKey = '__schema_version__';
  static const _schemaVersion = 2;

  /// Default freshness window: data younger than this is considered "fresh".
  static const Duration defaultFresh = Duration(minutes: 10);

  /// Default max age: data older than this is dropped (treated as missing).
  static const Duration defaultMaxAge = Duration(days: 1);

  bool _ready = false;

  Future<void> init() async {
    if (_ready) return;
    await Hive.initFlutter();
    final box = await Hive.openBox<String>(_box);

    // Schema versioning — purge if stale to avoid jsonDecode errors after backend changes.
    final stored = int.tryParse(box.get(_schemaKey) ?? '0') ?? 0;
    if (stored != _schemaVersion) {
      await box.clear();
      await box.put(_schemaKey, '$_schemaVersion');
    }
    _ready = true;
  }

  Box<String> get _b => Hive.box<String>(_box);

  Future<void> putJson(String key, Object payload) async {
    await _b.put(key, jsonEncode({
      'ts': DateTime.now().toIso8601String(),
      'data': payload,
    }));
  }

  /// Reads a previously stored entry, dropping it silently if older than [maxAge].
  ({DateTime fetchedAt, Object data})? readJson(
    String key, {
    Duration maxAge = defaultMaxAge,
  }) {
    final raw = _b.get(key);
    if (raw == null) return null;
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      final ts = DateTime.parse(map['ts'] as String);
      if (DateTime.now().difference(ts) > maxAge) return null;
      return (fetchedAt: ts, data: map['data'] as Object);
    } catch (_) {
      return null;
    }
  }

  /// Generic cache-aside helper.
  ///
  /// 1. Try the network via [fetch].
  /// 2. On success: store and return as fresh.
  /// 3. On failure: fall back to cached value if it exists and is younger than [maxAge].
  /// 4. Otherwise: rethrow.
  ///
  /// [fresh] only controls the `staleSinceFresh` flag — the network is still tried first.
  Future<CachedResult<T>> cached<T>({
    required String key,
    required Future<T> Function() fetch,
    required T Function(Object json) decode,
    required Object Function(T data) encode,
    Duration fresh = defaultFresh,
    Duration maxAge = defaultMaxAge,
  }) async {
    try {
      final data = await fetch();
      await putJson(key, encode(data));
      return CachedResult<T>(
        data: data,
        fromCache: false,
        fetchedAt: DateTime.now(),
        staleSinceFresh: false,
      );
    } catch (err) {
      final cached = readJson(key, maxAge: maxAge);
      if (cached == null) rethrow;
      return CachedResult<T>(
        data: decode(cached.data),
        fromCache: true,
        fetchedAt: cached.fetchedAt,
        staleSinceFresh: DateTime.now().difference(cached.fetchedAt) > fresh,
      );
    }
  }

  // ---- Simple key-value preferences (zone/block selections, theme, etc.) ----

  Future<void> putString(String key, String value) async => _b.put(key, value);

  String? getString(String key) => _b.get(key);

  Future<void> deleteString(String key) async => _b.delete(key);

  Future<void> clear() => _b.clear();
}
