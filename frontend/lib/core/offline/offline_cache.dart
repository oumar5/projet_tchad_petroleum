import 'dart:convert';

import 'package:hive_flutter/hive_flutter.dart';

class OfflineCache {
  OfflineCache._();
  static final OfflineCache instance = OfflineCache._();

  static const _box = 'sb.cache';
  bool _ready = false;

  Future<void> init() async {
    if (_ready) return;
    await Hive.initFlutter();
    await Hive.openBox<String>(_box);
    _ready = true;
  }

  Box<String> get _b => Hive.box<String>(_box);

  Future<void> putJson(String key, Object payload) async {
    await _b.put(key, jsonEncode({
      'ts': DateTime.now().toIso8601String(),
      'data': payload,
    }));
  }

  ({DateTime fetchedAt, Object data})? readJson(String key) {
    final raw = _b.get(key);
    if (raw == null) return null;
    final map = jsonDecode(raw) as Map<String, dynamic>;
    return (
      fetchedAt: DateTime.parse(map['ts'] as String),
      data: map['data'] as Object,
    );
  }

  Future<void> clear() => _b.clear();
}
